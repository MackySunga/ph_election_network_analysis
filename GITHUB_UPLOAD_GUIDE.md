# GitHub upload guide

This package is prepared for GitHub upload as a lightweight, reproducible source repository.

## What should be committed

Commit these:

- notebooks
- source code under `src/`
- Django dashboard code
- Docker files
- documentation files
- empty placeholder folders using `.gitkeep`
- optional static documentation under `docs/`

## What should not be committed

Do not commit these:

- raw CSV datasets under `data/raw/`
- processed generated CSVs under `data/processed/`
- generated outputs under `outputs/`
- executed notebook copies
- zip files
- local environment files
- database files

The `.gitignore` is already configured for this.

## Suggested first GitHub commands

```bash
git init
git add .
git status
git commit -m "Initial Docker-ready network science project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Before committing, confirm that large CSV files are not staged:

```bash
git status --short
```

If any file under `data/raw/`, `data/processed/`, or `outputs/` appears as staged, remove it from staging:

```bash
git restore --staged path/to/file
```

## Forker instructions

Forkers should clone the repository, place the required datasets into `data/raw/`, and run the notebook pipeline themselves using Docker.
