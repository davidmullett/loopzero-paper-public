from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "frozen" / "table1_domains.csv"
OUT = ROOT / "results" / "rendered" / "table1_domains.md"
OUT.parent.mkdir(parents=True, exist_ok=True)

def main() -> None:
    with SRC.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    headers = ["domain", "recursive_substrate", "operational_definition_of_collapse", "notes"]
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")

    for row in rows:
        lines.append("| " + " | ".join(row[h] for h in headers) + " |")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
