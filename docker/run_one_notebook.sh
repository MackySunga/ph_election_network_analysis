#!/usr/bin/env bash
set -euo pipefail
if [ $# -lt 1 ]; then
  echo "Usage: bash docker/run_one_notebook.sh notebooks/01_senate_results_inspection.ipynb"
  exit 1
fi
python docker/check_data.py
mkdir -p outputs/executed_notebooks outputs/run_logs
input_nb="$1"
base_name="$(basename "$input_nb")"
papermill "$input_nb" "outputs/executed_notebooks/$base_name" --cwd .
