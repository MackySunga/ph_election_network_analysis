#!/usr/bin/env bash
set -euo pipefail

python docker/check_data.py
mkdir -p outputs/executed_notebooks outputs/run_logs

NOTEBOOKS=(
  "00_start_here_setup_and_paths.ipynb"
  "01_senate_results_inspection.ipynb"
  "02_twitter_dataset_inspection_cleaning.ipynb"
  "03_known_authors_mapping.ipynb"
  "04_entity_extraction_candidate_dictionary.ipynb"
  "05_descriptive_communication_metrics.ipynb"
  "06_hashtag_cooccurrence_network.ipynb"
  "07_candidate_comention_network.ipynb"
  "08_candidate_hashtag_bipartite_network.ipynb"
  "09_mention_reply_network.ipynb"
  "10_network_metrics_vs_election_results.ipynb"
  "11_geographic_election_outcome_analysis.ipynb"
  "12_final_report_outputs.ipynb"
  "13_animated_storytelling_visuals.ipynb"
  "14_final_interpretive_analysis_and_discussion.ipynb"
  "15_phase2a_network_visual_explorer.ipynb"
)

for nb in "${NOTEBOOKS[@]}"; do
  echo "============================================================"
  echo "Running: notebooks/${nb}"
  echo "============================================================"
  papermill "notebooks/${nb}" "outputs/executed_notebooks/${nb}" --cwd .
done

echo ""
echo "All notebooks completed."
echo "Generated outputs are now in data/processed/ and outputs/."
echo "You may now run: docker compose up dashboard"
