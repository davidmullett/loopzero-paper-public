from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "results" / "frozen" / "table_s1_thresholds_public.csv"

def test_public_threshold_csv_exists():
    assert CSV_PATH.exists(), f"Missing {CSV_PATH}"

def test_public_threshold_csv_has_rows():
    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) >= 1, "Threshold CSV must contain at least one data row"
