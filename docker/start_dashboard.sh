#!/usr/bin/env bash
set -e
mkdir -p data/raw data/processed outputs/figures outputs/interactive outputs/tables outputs/networks outputs/report_assets outputs/run_logs
if [ ! -f "data/processed/comparison.csv" ]; then
  echo "WARNING: Generated outputs are missing."
  echo "Run the notebooks first before expecting dashboard charts and tables to appear."
  echo "Recommended command: docker compose run --rm jupyter bash docker/run_all_notebooks.sh"
fi
python manage.py check
python manage.py runserver 0.0.0.0:8000
