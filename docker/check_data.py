from pathlib import Path

expected = [
    "senate25-final_updated.csv",
    "for_export_philippine_elections.csv",
    "well_known_authors_philippine_elections.csv",
]
raw = Path("data/raw")
print("Dataset check")
print("-" * 60)
missing = []
for name in expected:
    path = raw / name
    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"OK      {name}  ({size_mb:.2f} MB)")
    else:
        print(f"MISSING {name}")
        missing.append(name)
print("-" * 60)
if missing:
    print("Place the missing CSV files in data/raw/ before running the notebooks.")
    raise SystemExit(1)
print("All expected raw datasets are present.")
