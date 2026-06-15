# Phase 4 package notes

This is the Docker-ready GitHub upload package.

## Design decision

The package intentionally excludes:

- raw datasets
- processed datasets
- generated visualizations
- generated report assets
- executed notebook output copies

This keeps the repository small and forces reproducibility: a forker must place the datasets in `data/raw/` and rerun the notebooks.

## Docker services

- `jupyter`: notebook execution and reproducibility environment
- `dashboard`: Django dashboard server

## Recommended public workflow

1. Upload this folder to GitHub.
2. Keep datasets out of GitHub.
3. In the README, tell forkers to place the CSVs in `data/raw/`.
4. Forkers run the notebooks with Docker.
5. Forkers generate their own outputs locally.
6. Forkers launch the dashboard after outputs are generated.

## Current version

Phase 4A Docker/GitHub source package.
