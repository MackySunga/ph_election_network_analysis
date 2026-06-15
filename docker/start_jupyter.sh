#!/usr/bin/env bash
set -e
mkdir -p data/raw data/processed outputs/figures outputs/interactive outputs/tables outputs/networks outputs/report_assets outputs/run_logs outputs/executed_notebooks
python docker/check_data.py || true
echo ""
echo "JupyterLab will start on: http://localhost:8888"
echo "Raw datasets should be placed in: data/raw/"
echo ""
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --ServerApp.token='' --ServerApp.password=''
