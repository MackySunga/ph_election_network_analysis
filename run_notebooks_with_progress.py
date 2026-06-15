
"""Run all project notebooks in order with terminal progress messages.

Usage from the project root:
    python run_notebooks_with_progress.py

This uses nbconvert. It is optional; you can still run notebooks manually in Jupyter.
"""
from pathlib import Path
import subprocess
import sys
import time

NOTEBOOKS = [
    "00_start_here_setup_and_paths.ipynb",
    "01_senate_results_inspection.ipynb",
    "02_twitter_dataset_inspection_cleaning.ipynb",
    "03_known_authors_mapping.ipynb",
    "04_entity_extraction_candidate_dictionary.ipynb",
    "05_descriptive_communication_metrics.ipynb",
    "06_hashtag_cooccurrence_network.ipynb",
    "07_candidate_comention_network.ipynb",
    "08_candidate_hashtag_bipartite_network.ipynb",
    "09_mention_reply_network.ipynb",
    "10_network_metrics_vs_election_results.ipynb",
    "11_geographic_election_outcome_analysis.ipynb",
    "12_final_report_outputs.ipynb",
    "13_animated_storytelling_visuals.ipynb",
    "14_final_interpretive_analysis_and_discussion.ipynb",
]

root = Path(__file__).resolve().parent
nb_dir = root / "notebooks"
log_dir = root / "outputs" / "run_logs"
log_dir.mkdir(parents=True, exist_ok=True)

start = time.time()
for i, nb_name in enumerate(NOTEBOOKS, 1):
    nb_path = nb_dir / nb_name
    if not nb_path.exists():
        print(f"[{i}/{len(NOTEBOOKS)}] SKIP missing {nb_name}")
        continue
    print("=" * 80)
    print(f"[{i}/{len(NOTEBOOKS)}] Running {nb_name}")
    t0 = time.time()
    cmd = [
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "notebook", "--execute", "--inplace", str(nb_path),
        "--ExecutePreprocessor.timeout=0",
    ]
    log_file = log_dir / f"runner_{nb_path.stem}.log"
    with log_file.open("w", encoding="utf-8") as f:
        proc = subprocess.run(cmd, cwd=root, stdout=f, stderr=subprocess.STDOUT)
    elapsed = time.time() - t0
    if proc.returncode != 0:
        print(f"FAILED {nb_name} after {elapsed:,.1f}s. Check {log_file}")
        sys.exit(proc.returncode)
    print(f"DONE {nb_name} in {elapsed:,.1f}s. Log: {log_file}")
print("=" * 80)
print(f"All notebooks completed in {time.time() - start:,.1f}s")
