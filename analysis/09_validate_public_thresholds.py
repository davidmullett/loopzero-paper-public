from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THRESHOLD_CSV = ROOT / "results" / "frozen" / "table_s1_thresholds_public.csv"

REQUIRED_COLUMNS = {
    "scope",
    "diversity_regime",
    "self_reinforcement_regime",
    "gain_regime",
    "notes",
}

def main() -> None:
    if not THRESHOLD_CSV.exists():
        raise FileNotFoundError(f"Missing {THRESHOLD_CSV}")

    with THRESHOLD_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - cols
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        rows = list(reader)
        if not rows:
            raise ValueError("Threshold CSV has no data rows")

        for i, row in enumerate(rows, start=1):
            for col in REQUIRED_COLUMNS:
                if not row.get(col):
                    raise ValueError(f"Empty value in row {i}, column '{col}'")

    print("Public threshold file is valid.")

if __name__ == "__main__":
    main()
