# Docker guide

This project is Docker-ready. Docker is the recommended environment for running the notebooks and dashboard consistently.

## 1. Build the containers

```bash
docker compose build
```

## 2. Add the datasets

Copy the required CSV files into:

```text
data/raw/
```

Then verify:

```bash
docker compose run --rm jupyter python docker/check_data.py
```

## 3. Run JupyterLab

```bash
docker compose up jupyter
```

Open:

```text
http://localhost:8888
```

The notebook server is configured without a token for local development.

## 4. Run the full notebook pipeline

```bash
docker compose run --rm jupyter bash docker/run_all_notebooks.sh
```

Executed notebook copies are saved under:

```text
outputs/executed_notebooks/
```

Generated CSVs, figures, network files, and HTML visualizations are saved under:

```text
data/processed/
outputs/
```

## 5. Run the Django dashboard

After running the notebooks:

```bash
docker compose up dashboard
```

Open:

```text
http://localhost:8000
```

If the dashboard is already open while notebooks are running, restart the dashboard after the notebooks finish so it reloads the generated files.

## 6. Run one notebook only

```bash
docker compose run --rm jupyter bash docker/run_one_notebook.sh notebooks/10_network_metrics_vs_election_results.ipynb
```
