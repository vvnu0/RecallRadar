from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

from flavor_data import COMPATIBILITY, DATASET_NOTES, INGREDIENTS, RECIPE_PASSAGES

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv('FLAVORMATRIX_DATA_DIR', BASE_DIR / 'data'))


def _split_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    delimiter = ';' if ';' in text else ','
    return [part.strip() for part in text.split(delimiter) if part.strip()]


def _normalize_ingredient(row: dict[str, Any], fallback_id: int) -> dict[str, Any]:
    molecules = row.get('molecules') or row.get('molecule_names') or row.get('molecule_list') or row.get('flavor_profile') or []
    return {
        'id': int(row.get('id') or row.get('entity_id') or fallback_id),
        'name': str(row.get('name') or row.get('ingredient') or row.get('entity_alias_readable') or row.get('ingredient_name') or '').strip(),
        'category': str(row.get('category') or row.get('entity_alias_basket') or row.get('ingredient_category') or 'Unknown').strip(),
        'cuisine': str(row.get('cuisine') or row.get('cuisine_type') or row.get('cluster') or 'Unspecified').strip(),
        'allergens': _split_list(row.get('allergens') or row.get('allergen_info')),
        'molecules': _split_list(molecules),
        'description': str(row.get('description') or row.get('entity_alias') or row.get('notes') or 'No description provided.').strip(),
    }


def _normalize_compatibility(row: dict[str, Any]) -> dict[str, Any]:
    return {
        'source': str(row.get('source') or row.get('ingredient_a') or row.get('query') or '').strip(),
        'target': str(row.get('target') or row.get('ingredient_b') or row.get('match') or '').strip(),
        'level': str(row.get('level') or row.get('compatibility') or row.get('label') or 'Unlabeled').strip(),
    }


def _normalize_passage(row: dict[str, Any], fallback_id: int) -> dict[str, Any]:
    text = row.get('text') or row.get('directions') or row.get('passage') or row.get('instructions') or ''
    title = row.get('title') or row.get('name') or row.get('recipe_name') or f'Passage {fallback_id}'
    ingredients = row.get('ingredients') or row.get('ner') or row.get('ingredient_names') or []
    return {
        'id': str(row.get('id') or row.get('recipe_id') or fallback_id),
        'source': str(row.get('source') or row.get('dataset') or 'dataset').strip(),
        'title': str(title).strip(),
        'text': str(text).strip(),
        'ingredients': _split_list(ingredients),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle))


def _first_existing(*candidates: str) -> Path | None:
    for candidate in candidates:
        path = DATA_DIR / candidate
        if path.exists():
            return path
    return None


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR))
    except ValueError:
        return str(path)


def _load_ingredient_records() -> tuple[list[dict[str, Any]], str]:
    path = _first_existing('flavordb_ingredients.json', 'flavordb_ingredients.csv', 'ingredients.json', 'ingredients.csv')
    if path is None:
        return INGREDIENTS, 'bundled sample'
    raw = _load_json(path) if path.suffix == '.json' else _load_csv(path)
    if isinstance(raw, dict):
        raw = raw.get('ingredients') or raw.get('data') or []
    records = [_normalize_ingredient(row, idx + 1) for idx, row in enumerate(raw)]
    records = [row for row in records if row['name'] and row['molecules']]
    return records or INGREDIENTS, _display_path(path)


def _load_compatibility_records() -> tuple[list[dict[str, Any]], str]:
    path = _first_existing('tastetrios.csv', 'tastetrios.json', 'compatibility.csv', 'compatibility.json')
    if path is None:
        return COMPATIBILITY, 'bundled sample'
    raw = _load_json(path) if path.suffix == '.json' else _load_csv(path)
    if isinstance(raw, dict):
        raw = raw.get('pairs') or raw.get('compatibility') or raw.get('data') or []
    records = [_normalize_compatibility(row) for row in raw]
    records = [row for row in records if row['source'] and row['target']]
    return records or COMPATIBILITY, _display_path(path)


def _load_recipe_records() -> tuple[list[dict[str, Any]], str]:
    path = _first_existing('recipenlg.jsonl', 'recipenlg.json', 'recipes.json', 'recipenlg.csv')
    if path is None:
        return RECIPE_PASSAGES, 'bundled sample'
    if path.suffix == '.jsonl':
        raw = _load_jsonl(path)
    elif path.suffix == '.json':
        raw = _load_json(path)
    else:
        raw = _load_csv(path)
    if isinstance(raw, dict):
        raw = raw.get('recipes') or raw.get('data') or raw.get('passages') or []
    records = [_normalize_passage(row, idx + 1) for idx, row in enumerate(raw)]
    records = [row for row in records if row['text']]
    return records or RECIPE_PASSAGES, _display_path(path)


def load_flavor_matrix_data() -> dict[str, Any]:
    ingredients, ingredient_source = _load_ingredient_records()
    compatibility, compatibility_source = _load_compatibility_records()
    passages, recipe_source = _load_recipe_records()
    dataset_notes = dict(DATASET_NOTES)
    dataset_notes['flavordb'] = f"{dataset_notes['flavordb']} Active source: {ingredient_source}."
    dataset_notes['tastetrios'] = f"{dataset_notes['tastetrios']} Active source: {compatibility_source}."
    dataset_notes['recipenlg'] = f"{dataset_notes['recipenlg']} Active source: {recipe_source}."
    dataset_notes['data_directory'] = f"FlavorMatrix looks for datasets in {DATA_DIR}."
    return {
        'ingredients': ingredients,
        'compatibility': compatibility,
        'passages': passages,
        'dataset_notes': dataset_notes,
    }
