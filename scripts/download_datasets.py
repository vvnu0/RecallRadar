"""
Download and prepare raw datasets for FlavorMatrix.

Sources:
  - FlavorDB:   cosylab.iiitd.edu.in/flavordb  (scraped via REST API)
  - TasteTrios: Kaggle dataset mbsssb/tastetrios
  - RecipeNLG:  Kaggle dataset paultimothymooney/recipenlg  (large ~2 GB)
  - FOODPUZZLE: HuggingFace dataset (placeholder – manual download)

Usage:
    python scripts/download_datasets.py          # download all available
    python scripts/download_datasets.py flavordb  # download only FlavorDB
"""

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
load_dotenv()

# ---------------------------------------------------------------------------
# FlavorDB scraper (public REST API)
# ---------------------------------------------------------------------------

FLAVORDB_BASE = "https://cosylab.iiitd.edu.in/flavordb"


def _get_json(url: str, retries: int = 3, delay: float = 1.0):
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                raise RuntimeError(f"Failed to fetch {url}: {e}")


def _download_kaggle_fallback(dataset: str, out_dir: Path) -> bool:
    """
    Download a dataset via kagglehub into out_dir.

    Returns True on success, False otherwise.
    """
    # First, hydrate Kaggle credentials from .env if provided.
    _ensure_kaggle_credentials_from_env()

    # Then try kagglehub python package.
    try:
        import kagglehub
        path = kagglehub.dataset_download(dataset)
        print(f"  Downloaded Kaggle dataset via kagglehub: {dataset} -> {path}")
        for f in Path(path).rglob("*"):
            if f.is_file():
                dest = out_dir / f.name
                shutil.copy2(f, dest)
                print(f"    -> {dest.name}")
        return True
    except ImportError:
        print("  [warn] kagglehub not installed. Trying Kaggle CLI fallback …")
    except Exception as e:
        print(f"  [warn] kagglehub download failed ({dataset}): {e}")
        print("  Trying Kaggle CLI fallback …")

    # Fallback to kaggle CLI if installed/configured
    tmp_dir = out_dir / "_kaggle_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "kaggle",
        "datasets",
        "download",
        "-d",
        dataset,
        "-p",
        str(tmp_dir),
        "--unzip",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        copied = 0
        for f in tmp_dir.rglob("*"):
            if f.is_file():
                dest = out_dir / f.name
                shutil.copy2(f, dest)
                copied += 1
                print(f"    -> {dest.name}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        if copied == 0:
            print(f"  [warn] Kaggle CLI ran, but no files were found for {dataset}.")
            return False
        print(f"  Downloaded Kaggle dataset via CLI: {dataset} ({copied} files)")
        return True
    except FileNotFoundError:
        print("  [warn] Kaggle CLI not found. Install with: pip install kaggle")
        print("         Then run: kaggle datasets download -d <dataset> --unzip")
        return False
    except subprocess.CalledProcessError as e:
        print(f"  [warn] Kaggle CLI download failed ({dataset}).")
        if e.stderr:
            print(f"         {e.stderr.strip()}")
        print("         Ensure Kaggle API credentials are configured.")
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _ensure_kaggle_credentials_from_env():
    """
    Ensure Kaggle auth is available from environment variables.

    Supported .env keys:
      - KAGGLE_USERNAME
      - KAGGLE_KEY

    If both are present, this function exports them to process env and writes
    ~/.kaggle/kaggle.json if missing.
    """
    username = os.getenv("KAGGLE_USERNAME", "").strip()
    key = os.getenv("KAGGLE_KEY", "").strip()
    if not username or not key:
        return

    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = key

    kaggle_dir = Path.home() / ".kaggle"
    kaggle_json = kaggle_dir / "kaggle.json"
    if not kaggle_json.exists():
        kaggle_dir.mkdir(parents=True, exist_ok=True)
        with open(kaggle_json, "w", encoding="utf-8") as f:
            json.dump({"username": username, "key": key}, f)
        try:
            os.chmod(kaggle_json, 0o600)
        except Exception:
            # chmod may be restricted on some Windows setups; safe to ignore.
            pass


def download_flavordb() -> bool:
    """Scrape FlavorDB entity list and per-entity molecule details."""
    out_dir = RAW_DIR / "flavordb"
    out_dir.mkdir(parents=True, exist_ok=True)

    entities_file = out_dir / "entities.json"
    details_file = out_dir / "entity_details.json"

    # Step 1: entity list (legacy API path, may be unavailable)
    try:
        if entities_file.exists():
            print(f"  [skip] {entities_file} already exists")
            with open(entities_file) as f:
                entities = json.load(f)
        else:
            print("  Fetching entity list from FlavorDB …")
            entities = _get_json(f"{FLAVORDB_BASE}/food_entities")
            with open(entities_file, "w") as f:
                json.dump(entities, f)
            print(f"  Saved {len(entities)} entities -> {entities_file}")

        # Step 2: per-entity details (molecules)
        if details_file.exists():
            print(f"  [skip] {details_file} already exists")
            return True

        details = []
        total = len(entities)
        print(f"  Fetching details for {total} entities (this may take a few minutes) …")
        for i, ent in enumerate(entities):
            eid = ent.get("entity_id") or ent.get("id")
            if eid is None:
                continue
            try:
                d = _get_json(f"{FLAVORDB_BASE}/entities_details?id={eid}")
                details.append(d)
            except RuntimeError:
                print(f"    [warn] Could not fetch entity {eid}, skipping")
            if (i + 1) % 50 == 0 or i + 1 == total:
                print(f"    {i + 1}/{total}")
            time.sleep(0.25)

        with open(details_file, "w") as f:
            json.dump(details, f)
        print(f"  Saved {len(details)} entity details -> {details_file}")
        return True
    except RuntimeError as e:
        print(f"  [warn] FlavorDB web API unavailable: {e}")
        print("  Trying Kaggle mirror fallback: rayenoaf/flavourdb2")

    # Fallback: Kaggle mirror (newer and more stable source)
    ok = _download_kaggle_fallback("rayenoaf/flavourdb2", out_dir)
    if not ok:
        print("  [warn] Could not download FlavorDB automatically.")
        print("  Manually place FlavorDB/FlavorDB2 files into data/raw/flavordb/")
    return ok


# ---------------------------------------------------------------------------
# TasteTrios (Kaggle)
# ---------------------------------------------------------------------------

def download_tastetrios() -> bool:
    """Download TasteTrios ingredient-compatibility dataset from Kaggle."""
    out_dir = RAW_DIR / "tastetrios"
    out_dir.mkdir(parents=True, exist_ok=True)

    marker = out_dir / ".downloaded"
    if marker.exists():
        print(f"  [skip] TasteTrios already downloaded")
        return True

    # Try the original dataset ID first, then a known public mirror.
    ok = _download_kaggle_fallback("mbsssb/tastetrios", out_dir)
    if not ok:
        print("  Trying alternate public dataset id: uom190346a/tastetrios-exploring-ingredient-combinations")
        ok = _download_kaggle_fallback(
            "uom190346a/tastetrios-exploring-ingredient-combinations",
            out_dir,
        )
    if ok:
        marker.touch()
    else:
        print("  [warn] Manually download mbsssb/tastetrios to data/raw/tastetrios/")
    return ok


# ---------------------------------------------------------------------------
# RecipeNLG (Kaggle – large dataset)
# ---------------------------------------------------------------------------

def download_recipenlg() -> bool:
    """Download RecipeNLG recipe corpus from Kaggle."""
    out_dir = RAW_DIR / "recipenlg"
    out_dir.mkdir(parents=True, exist_ok=True)

    marker = out_dir / ".downloaded"
    if marker.exists():
        print(f"  [skip] RecipeNLG already downloaded")
        return True

    ok = _download_kaggle_fallback("paultimothymooney/recipenlg", out_dir)
    if ok:
        marker.touch()
    else:
        print("  [warn] Manually download paultimothymooney/recipenlg to data/raw/recipenlg/")
    return ok


# ---------------------------------------------------------------------------
# FOODPUZZLE benchmark (placeholder)
# ---------------------------------------------------------------------------

def download_foodpuzzle() -> bool:
    """Placeholder for FOODPUZZLE benchmark data."""
    out_dir = RAW_DIR / "foodpuzzle"
    out_dir.mkdir(parents=True, exist_ok=True)

    marker = out_dir / ".downloaded"
    if marker.exists():
        print(f"  [skip] FOODPUZZLE already downloaded")
        return True

    print("  FOODPUZZLE requires manual download.")
    print("  Place benchmark JSON/CSV files in data/raw/foodpuzzle/")
    print("  Expected format: JSON with fields 'question', 'expected_answer', 'source'")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

DOWNLOADERS = {
    "flavordb": download_flavordb,
    "tastetrios": download_tastetrios,
    "recipenlg": download_recipenlg,
    "foodpuzzle": download_foodpuzzle,
}


def main():
    parser = argparse.ArgumentParser(description="Download FlavorMatrix datasets")
    parser.add_argument(
        "datasets",
        nargs="*",
        choices=list(DOWNLOADERS.keys()),
        help="Datasets to download (default: all)",
    )
    args = parser.parse_args()
    selected = args.datasets or list(DOWNLOADERS.keys())

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    failed = []
    for name in selected:
        print(f"\n{'='*60}")
        print(f" Downloading: {name}")
        print(f"{'='*60}")
        try:
            ok = DOWNLOADERS[name]()
            if ok is False:
                failed.append(name)
        except Exception as e:
            failed.append(name)
            print(f"  [error] {name} failed: {e}")

    if failed:
        print(f"\nCompleted with failures: {', '.join(failed)}")
        print("Fix the failed datasets, then rerun this downloader.")
        raise SystemExit(1)
    else:
        print("\nAll requested dataset downloads completed.")
    print("Next step: python scripts/build_duckdb.py")


if __name__ == "__main__":
    main()
