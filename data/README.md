# FlavorMatrix dataset dropzone

Place your real project datasets in this directory so the Flask app loads them instead of the bundled sample fallback.

## Supported filenames

### FlavorDB-style ingredients
Use one of:
- `flavordb_ingredients.json`
- `flavordb_ingredients.csv`
- `ingredients.json`
- `ingredients.csv`

Expected fields (best effort mapper):
- `id`
- `name` or `ingredient`
- `category`
- `cuisine`
- `allergens`
- `molecules` (comma- or semicolon-separated string, or JSON list)
- `description`

### TasteTrios-style compatibility labels
Use one of:
- `tastetrios.csv`
- `tastetrios.json`
- `compatibility.csv`
- `compatibility.json`

Expected fields:
- `source`
- `target`
- `level`

### RecipeNLG / corpus passages
Use one of:
- `recipenlg.jsonl`
- `recipenlg.json`
- `recipes.json`
- `recipenlg.csv`

Expected fields:
- `id`
- `title`
- `text`
- `ingredients`
- `source`

If these files are missing, FlavorMatrix falls back to the bundled sample data in `src/flavor_data.py` so the app still boots.
