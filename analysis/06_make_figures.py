from __future__ import annotations

import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "frozen" / "fig3_leadtime_source.csv"
OUT = ROOT / "results" / "rendered" / "figure3_leadtime.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

COLORS = {
    "Loopzero": "#444444",
    "Variance": "#888888",
    "AC1": "#BBBBBB",
}

def parse_median(value: str) -> float | None:
    if value is None or value == "":
        return None
    return float(value)

def main() -> None:
    with SRC.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    grouped = defaultdict(list)
    max_dt = 0.0

    for row in rows:
        grouped[row["domain"]].append(row)
        v = parse_median(row["median_dt"])
        if v is not None:
            max_dt = max(max_dt, v)

    domains = list(grouped.keys())
    width = 1200
    left = 220
    top = 40
    row_h = 22
    gap = 10
    block_h = row_h * 3 + gap + 16
    height = top + len(domains) * block_h + 40
    plot_w = width - left - 60

    def xscale(v: float) -> float:
        return left + (v / max_dt) * plot_w if max_dt else left

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">')
    svg.append('<style>text{font-family:Arial,Helvetica,sans-serif;font-size:12px;fill:#222}</style>')
    svg.append(f'<text x="{left}" y="20">Figure 3. Lead-time source (publication-grade rendering)</text>')

    # x-axis ticks
    for tick in [0, 100, 200, 300, 400]:
        if tick <= max_dt:
            x = xscale(tick)
            svg.append(f'<line x1="{x}" y1="{top-5}" x2="{x}" y2="{height-20}" stroke="#e0e0e0" stroke-width="1"/>')
            svg.append(f'<text x="{x-8}" y="{height-5}">{tick}</text>')

    y = top
    for domain in domains:
        svg.append(f'<text x="10" y="{y+16}">{domain}</text>')
        rows_for_domain = grouped[domain]

        order = {"Loopzero": 0, "Variance": 1, "AC1": 2}
        rows_for_domain = sorted(rows_for_domain, key=lambda r: order.get(r["method"], 99))

        for i, row in enumerate(rows_for_domain):
            yy = y + i * row_h
            method = row["method"]
            val = parse_median(row["median_dt"])
            accepted = row["accepted"]

            svg.append(f'<text x="{left-110}" y="{yy+14}">{method}</text>')

            if val is not None and accepted == "yes":
                bar_w = xscale(val) - left
                fill = COLORS.get(method, "#999999")
                svg.append(f'<rect x="{left}" y="{yy}" width="{bar_w}" height="14" fill="{fill}"/>')
                svg.append(f'<text x="{left + bar_w + 6}" y="{yy+12}">{int(val)}</text>')
            else:
                svg.append(f'<text x="{left}" y="{yy+12}">not accepted</text>')

        y += block_h

    svg.append('</svg>')
    OUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
