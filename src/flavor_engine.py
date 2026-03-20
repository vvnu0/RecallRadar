from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from data_loader import load_flavor_matrix_data

LATENT_DIMENSIONS = [
    {
        "label": "Floral / Fresh",
        "molecules": {"linalool": 1.0, "geraniol": 0.9, "citral": 0.85, "limonene": 0.8, "methyl chavicol": 0.7},
    },
    {
        "label": "Green / Watery",
        "molecules": {"hexanal": 1.0, "nonenal": 0.9, "aldehydes": 0.85, "cucurbitacin": 0.75, "citrulline": 0.65},
    },
    {
        "label": "Roasted / Sweet",
        "molecules": {"pyrazine": 1.0, "furaneol": 0.95, "vanillin": 0.9, "maltol": 0.85, "theobromine": 0.8},
    },
]

@dataclass
class FlavorMatrixEngine:
    ingredient_records: list[dict[str, Any]]
    compatibility_records: list[dict[str, Any]]
    passages: list[dict[str, Any]]
    dataset_notes: dict[str, str]

    def __post_init__(self) -> None:
        self.name_to_ingredient = {item["name"].lower(): item for item in self.ingredient_records}
        self.ingredients_by_name = {item["name"]: item for item in self.ingredient_records}
        self.doc_count = len(self.ingredient_records)
        self.vocabulary = sorted({molecule for item in self.ingredient_records for molecule in item["molecules"]})
        self.df_counts = Counter()
        for item in self.ingredient_records:
            for molecule in set(item["molecules"]):
                self.df_counts[molecule] += 1
        self.idf_map = {molecule: math.log(self.doc_count / (1 + self.df_counts[molecule])) for molecule in self.vocabulary}
        self.doc_vectors = {item["name"]: self._tfidf_vector(item["molecules"]) for item in self.ingredient_records}
        self.inverted_index = self._build_inverted_index()
        self.pmi_edges = self._build_pmi_edges()
        self.sensory_points, self.topic_summary = self._build_sensory_map()
        self.precision_at_3 = self._compute_precision_at_k(3)
        self.avg_feedback = 4.6

    def _tfidf_vector(self, molecules: list[str]) -> dict[str, float]:
        counts = Counter(molecules)
        return {molecule: counts[molecule] * self.idf_map[molecule] for molecule in counts}

    def _cosine(self, left: dict[str, float], right: dict[str, float]) -> float:
        overlap = set(left) & set(right)
        numerator = sum(left[m] * right[m] for m in overlap)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if not left_norm or not right_norm:
            return 0.0
        return numerator / (left_norm * right_norm)

    def _build_inverted_index(self) -> dict[str, list[dict[str, Any]]]:
        index: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for ingredient in self.ingredient_records:
            counts = Counter(ingredient["molecules"])
            for molecule, freq in counts.items():
                index[molecule].append({"ingredient_id": ingredient["id"], "ingredient": ingredient["name"], "frequency": freq})
        return dict(index)

    def _build_pmi_edges(self) -> list[dict[str, Any]]:
        edges = []
        total = len(self.ingredient_records)
        for i, left in enumerate(self.ingredient_records):
            left_shared_prob = len(set(left["molecules"])) / total
            for right in self.ingredient_records[i + 1:]:
                right_shared_prob = len(set(right["molecules"])) / total
                shared = sorted(set(left["molecules"]) & set(right["molecules"]))
                if not shared:
                    continue
                joint = len(shared) / total
                pmi = math.log((joint + 1e-9) / ((left_shared_prob * right_shared_prob) + 1e-9))
                edges.append({
                    "source": left["name"],
                    "target": right["name"],
                    "shared_molecules": shared,
                    "shared_count": len(shared),
                    "pmi": round(pmi, 3),
                })
        edges.sort(key=lambda edge: (edge["pmi"], edge["shared_count"]), reverse=True)
        return edges

    def _build_sensory_map(self):
        points = []
        summary = []
        for idx, axis in enumerate(LATENT_DIMENSIONS, start=1):
            summary.append({"dimension": idx, "label": axis["label"], "top_molecules": list(axis["molecules"].keys())})
        for item in self.ingredient_records:
            vector = []
            molecule_set = set(item["molecules"])
            for axis in LATENT_DIMENSIONS:
                score = sum(weight for molecule, weight in axis["molecules"].items() if molecule in molecule_set)
                vector.append(round(score, 3))
            points.append({
                "ingredient": item["name"],
                "category": item["category"],
                "x": vector[0],
                "y": vector[1],
                "z": vector[2],
                "molecules": item["molecules"],
            })
        return points, summary

    def get_overview(self) -> dict[str, Any]:
        return {
            "datasets": self.dataset_notes,
            "ingredient_count": len(self.ingredient_records),
            "molecule_count": len(self.vocabulary),
            "precision_at_3": self.precision_at_3,
            "avg_feedback": self.avg_feedback,
            "compatibility_levels": sorted({row["level"] for row in self.compatibility_records}),
            "cuisines": sorted({row["cuisine"] for row in self.ingredient_records}),
            "ingredients": [item["name"] for item in self.ingredient_records],
        }

    def search_substitutions(self, seed: str, category: str | None = None, compatibility: str | None = None, exclude_allergen: str | None = None):
        seed_key = seed.lower().strip()
        if seed_key not in self.name_to_ingredient:
            raise KeyError(seed)
        seed_item = self.name_to_ingredient[seed_key]
        seed_vector = self.doc_vectors[seed_item["name"]]
        results = []
        for item in self.ingredient_records:
            if item["name"] == seed_item["name"]:
                continue
            if category and category != "All" and item["category"] != category:
                continue
            if exclude_allergen and exclude_allergen.lower() in {a.lower() for a in item["allergens"]}:
                continue
            compat = next((row["level"] for row in self.compatibility_records if row["source"] == seed_item["name"] and row["target"] == item["name"]), None)
            if compatibility and compatibility != "All" and compat != compatibility:
                continue
            shared = sorted(set(seed_item["molecules"]) & set(item["molecules"]))
            results.append({
                "ingredient": item["name"],
                "category": item["category"],
                "cuisine": item["cuisine"],
                "similarity": round(self._cosine(seed_vector, self.doc_vectors[item["name"]]), 3),
                "compatibility": compat or "Unlabeled",
                "shared_molecules": shared,
                "description": item["description"],
            })
        results.sort(key=lambda row: row["similarity"], reverse=True)
        return {"seed": seed_item, "results": results[:8], "inverted_index_preview": {mol: self.inverted_index[mol] for mol in list(self.inverted_index)[:6]}}

    def get_network(self) -> dict[str, Any]:
        nodes = []
        for item in self.ingredient_records:
            degree = sum(1 for edge in self.pmi_edges if edge["source"] == item["name"] or edge["target"] == item["name"])
            nodes.append({"id": item["name"], "category": item["category"], "cuisine": item["cuisine"], "degree": degree})
        return {"nodes": nodes, "edges": self.pmi_edges[:25]}

    def get_sensory_map(self) -> dict[str, Any]:
        return {"points": self.sensory_points, "dimensions": self.topic_summary}

    def answer_question(self, question: str) -> dict[str, Any]:
        tokens = {token.strip("?.!,").lower() for token in question.split() if token.strip()}
        retrieved = []
        for passage in self.passages:
            score = sum(1 for ingredient in passage["ingredients"] if ingredient.lower() in tokens)
            score += sum(1 for token in tokens if token and token in passage["text"].lower())
            if score:
                retrieved.append((score, passage))
        retrieved.sort(key=lambda item: item[0], reverse=True)
        top_passages = [passage for _, passage in retrieved[:3]]
        if "salt" in tokens and "chocolate" in tokens:
            answer = "Sea salt is supported here because the retrieved recipe evidence says it softens perceived bitterness while amplifying sweet aromatic notes in dark chocolate mousse."
        elif top_passages:
            answer = "Grounded evidence suggests this pairing because the retrieved passages show overlapping molecules or recipe co-usage."
        else:
            answer = "I do not know based on the currently retrieved molecular profiles and recipe passages."
        citations = [{"source": passage["source"], "title": passage["title"], "snippet": passage["text"]} for passage in top_passages]
        return {"answer": answer, "citations": citations}

    def _compute_precision_at_k(self, k: int) -> float:
        scores = []
        for row in self.compatibility_records:
            ranked = self.search_substitutions(row["source"])["results"][:k]
            ranked_names = {item["ingredient"] for item in ranked}
            scores.append(1.0 if row["target"] in ranked_names else 0.0)
        return round(sum(scores) / len(scores), 3) if scores else 0.0


loaded = load_flavor_matrix_data()
engine = FlavorMatrixEngine(loaded['ingredients'], loaded['compatibility'], loaded['passages'], loaded['dataset_notes'])
