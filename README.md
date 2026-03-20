# FlavorMatrix

FlavorMatrix is a Flask-deployable molecular gastronomy dashboard that replaces the starter Kardashian search template with a culinary retrieval and explainability experience.

## What changed

- The app now **loads dataset files from `data/` first** instead of hardcoding ingredients directly into the engine.
- The bundled records in `src/flavor_data.py` are now only a **fallback sample dataset** used when your real files are missing.
- The active data source is exposed in the UI via the dataset notes panel and in `/api/overview`.

## Supported datasets

FlavorMatrix currently looks for the following files inside `data/`:

- Ingredient corpus: `flavordb_ingredients.json`, `flavordb_ingredients.csv`, `ingredients.json`, or `ingredients.csv`
- Compatibility labels: `tastetrios.csv`, `tastetrios.json`, `compatibility.csv`, or `compatibility.json`
- Recipe / RAG passages: `recipenlg.jsonl`, `recipenlg.json`, `recipes.json`, or `recipenlg.csv`

See `data/README.md` for the accepted columns and shapes.

## Run locally

```bash
pip install -r requirements.txt
python src/app.py
```

Then open `http://localhost:5001`.

## Important note

If you want the dashboard to use the real FlavorDB / TasteTrios / RecipeNLG data, add those exported files into `data/` using one of the supported filenames above. The app will automatically ingest them on startup.
