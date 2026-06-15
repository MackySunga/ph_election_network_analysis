# Dataset setup

This repository does not include raw datasets.

## Required raw files

| Required filename | Purpose | Place in |
|---|---|---|
| `senate25-final_updated.csv` | Actual 2025 Philippine Senate election results | `data/raw/` |
| `for_export_philippine_elections.csv` | Twitter/X election discourse dataset | `data/raw/` |
| `well_known_authors_philippine_elections.csv` | Known-author mapping file | `data/raw/` |

## Why the datasets are ignored

The Twitter/X and election result files are large. They are excluded from GitHub so the repository remains clean and forkable. Forkers should obtain or place the datasets locally, then run the notebooks themselves.

## Expected workflow for forkers

```bash
# 1. Clone/fork the repository
# 2. Copy the three CSV files into data/raw/
# 3. Verify files
docker compose run --rm jupyter python docker/check_data.py

# 4. Run notebooks
docker compose run --rm jupyter bash docker/run_all_notebooks.sh

# 5. Start dashboard
docker compose up dashboard
```
