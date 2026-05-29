from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "frozen" / "table2_equal_fp.csv"
OUT = ROOT / "results" / "rendered" / "table2_equal_fp.md"
OUT.parent.mkdir(parents=True, exist_ok=True)

def main() -> None:
    with SRC.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    headers = [
        "domain",
        "dt_predicate_median",
        "dt_predicate_iqr",
        "n_pred",
        "accepted_var_baseline",
        "accepted_var_id",
        "dt_var_median",
        "dt_var_iqr",
        "n_var",
        "accepted_ac1_baseline",
        "accepted_ac1_id",
        "dt_ac1_median",
        "dt_ac1_iqr",
        "n_ac1",
        "notes",
    ]

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")

    for row in rows:
        lines.append("| " + " | ".join(row.get(h, "") for h in headers) + " |")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
