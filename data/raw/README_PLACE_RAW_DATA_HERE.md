# Raw data folder

The raw CSV datasets are intentionally **not included** in this GitHub-ready repository because they are large and should not be committed.

Place these files here before running the notebooks:

1. `senate25-final_updated.csv`
2. `for_export_philippine_elections.csv`
3. `well_known_authors_philippine_elections.csv`

After adding the files, the folder should look like this:

```text
data/raw/
├── senate25-final_updated.csv
├── for_export_philippine_elections.csv
└── well_known_authors_philippine_elections.csv
```

Run this check:

```bash
docker compose run --rm jupyter python docker/check_data.py
```
