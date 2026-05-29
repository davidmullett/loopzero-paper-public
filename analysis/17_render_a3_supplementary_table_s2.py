#!/usr/bin/env python3
"""
analysis/17_render_a3_supplementary_table_s2.py

Render polished Supplementary Table S2 from a3_effect_sizes_full.csv.

Reads:  results/rendered/effect_sizes/a3_effect_sizes_full.csv
Writes: results/rendered/effect_sizes/a3_supplementary_table_s2.md

Format: per-benchmark sections (Markets, Recsys h=40, h=50 canonical, h=60),
each with a 3-row x 3-column table (witness x effect measure). Canonical
group is bolded. BCa CIs are primary. A separate sensitivity table flags
cells where BCa and percentile CIs diverge by >= 0.05 on either endpoint.
"""
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "results" / "rendered" / "effect_sizes" / "a3_effect_sizes_full.csv"
OUT_PATH = REPO_ROOT / "results" / "rendered" / "effect_sizes" / "a3_supplementary_table_s2.md"


BENCH_ORDER = [
    ("volmageddon_covid_public_v2", "Markets (Volmageddon + COVID-MWCB)"),
    ("movielens25m_recursive_frontier_public_v1__horizon_40", "Recsys h=40 (off-pre-reg)"),
    ("movielens25m_recursive_frontier_public_v1__canonical_h50", "Recsys h=50 (canonical, pre-registered)"),
    ("movielens25m_recursive_frontier_public_v1__horizon_60", "Recsys h=60 (off-pre-reg)"),
]
CANONICAL = "movielens25m_recursive_frontier_public_v1__canonical_h50"

WITNESS_ORDER = ["G", "p", "delta"]
WITNESS_LABEL = {"G": "G", "p": "p", "delta": "\u03b4"}


def bench_short(benchmark_id):
    if "volmageddon" in benchmark_id:
        return "Markets"
    if "horizon_40" in benchmark_id:
        return "Recsys h=40"
    if "canonical_h50" in benchmark_id:
        return "Recsys h=50"
    if "horizon_60" in benchmark_id:
        return "Recsys h=60"
    return benchmark_id


def fmt_signed(point, lo, hi):
    return f"{point:+.3f} [{lo:+.3f}, {hi:+.3f}]"


def fmt_auc(point, lo, hi):
    return f"{point:.3f} [{lo:.3f}, {hi:.3f}]"


df = pd.read_csv(CSV_PATH)

lines = []
lines.append("# Supplementary Table S2 \u2014 Effect sizes with bootstrap 95% BCa CIs")
lines.append("")
lines.append("**Source:** `results/rendered/effect_sizes/a3_effect_sizes_full.csv` (commit `d8908dd`)  ")
lines.append("**Generator:** `analysis/17_render_a3_supplementary_table_s2.py`")
lines.append("")
lines.append(
    "Per-witness (G, p, \u03b4) effect sizes at each benchmark/horizon with 95% BCa "
    "confidence intervals from cluster-aware bootstrap (10,000 iterations). Cohen's d, "
    "Glass's d, and Rank AUC are reported as complementary magnitude metrics. BCa is the "
    "primary CI method; percentile CIs are reported alongside for the cells where they "
    "differ meaningfully (sensitivity section below)."
)
lines.append("")

# Sign convention
lines.append("## Sign convention")
lines.append("")
lines.append("Predicted direction by witness (event vs control):")
lines.append("")
lines.append("- **G** (amplification): event > control predicted; positive d / AUC > 0.5 confirms")
lines.append("- **p** (concentration): event > control predicted; positive d / AUC > 0.5 confirms")
lines.append("- **\u03b4** (contraction): event < control predicted; negative d / AUC < 0.5 confirms")
lines.append("")

# Bootstrap unit grain
lines.append("## Bootstrap unit grain")
lines.append("")
lines.append("- **Markets:** segment-level resampling (n = 38 controls + 16 events; ~30 rows per segment)")
lines.append("- **Recsys** (all horizons): user-level resampling (n \u2248 40,339 user clusters; 10 rows per cluster)")
lines.append("")

# Effect sizes by benchmark
lines.append("## Effect sizes by benchmark")
lines.append("")

for bench_id, bench_label in BENCH_ORDER:
    is_canon = bench_id == CANONICAL
    header = f"### **{bench_label}**" if is_canon else f"### {bench_label}"
    lines.append(header)
    lines.append("")
    lines.append("| Witness | Cohen's d [BCa 95% CI] | Glass's d [BCa 95% CI] | Rank AUC [BCa 95% CI] |")
    lines.append("|---|---|---|---|")

    sub = df[df.benchmark_id == bench_id]
    for witness in WITNESS_ORDER:
        cohens = sub[(sub.witness == witness) & (sub.effect_measure == "cohens_d")].iloc[0]
        glasss = sub[(sub.witness == witness) & (sub.effect_measure == "glasss_d")].iloc[0]
        auc = sub[(sub.witness == witness) & (sub.effect_measure == "rank_auc")].iloc[0]

        wlbl = WITNESS_LABEL[witness]
        c_str = fmt_signed(cohens.point_estimate, cohens.ci_lower_bca, cohens.ci_upper_bca)
        g_str = fmt_signed(glasss.point_estimate, glasss.ci_lower_bca, glasss.ci_upper_bca)
        a_str = fmt_auc(auc.point_estimate, auc.ci_lower_bca, auc.ci_upper_bca)

        if is_canon:
            wlbl = f"**{wlbl}**"
            c_str = f"**{c_str}**"
            g_str = f"**{g_str}**"
            a_str = f"**{a_str}**"

        lines.append(f"| {wlbl} | {c_str} | {g_str} | {a_str} |")
    lines.append("")

# BCa vs percentile sensitivity
lines.append("## BCa-vs-percentile sensitivity")
lines.append("")
lines.append(
    "BCa correction matters where the bootstrap distribution is skewed (small n; "
    "right-skewed tails on small-n p-witness). Cells where |BCa endpoint \u2212 percentile "
    "endpoint| \u2265 0.05 on either side:"
)
lines.append("")
lines.append("| Benchmark | Witness | Measure | Percentile CI | BCa CI | max \u0394 |")
lines.append("|---|---|---|---|---|---|")

threshold = 0.05
sensitivity_rows = []
for _, row in df.iterrows():
    d_lo = abs(row.ci_lower_bca - row.ci_lower_percentile)
    d_hi = abs(row.ci_upper_bca - row.ci_upper_percentile)
    max_d = max(d_lo, d_hi)
    if max_d >= threshold:
        if row.effect_measure == "rank_auc":
            pct = f"[{row.ci_lower_percentile:.3f}, {row.ci_upper_percentile:.3f}]"
            bca = f"[{row.ci_lower_bca:.3f}, {row.ci_upper_bca:.3f}]"
        else:
            pct = f"[{row.ci_lower_percentile:+.3f}, {row.ci_upper_percentile:+.3f}]"
            bca = f"[{row.ci_lower_bca:+.3f}, {row.ci_upper_bca:+.3f}]"
        sensitivity_rows.append(
            (bench_short(row.benchmark_id), WITNESS_LABEL[row.witness],
             row.effect_measure, pct, bca, max_d)
        )

sensitivity_rows.sort(key=lambda r: -r[5])
if sensitivity_rows:
    for r in sensitivity_rows:
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]:.2f} |")
else:
    lines.append("| _(no cells exceed threshold)_ |  |  |  |  |  |")
lines.append("")

# Notes
lines.append("## Notes")
lines.append("")
lines.append(
    "- **Recsys BCa correction is empirically negligible.** Across all 27 recsys cells "
    "at n \u2248 40K, |BCa \u2212 percentile| < 0.01 on every endpoint. Consistent with "
    "BCa's O(1/\u221an) second-order correction theory: at this n the correction is below "
    "the bootstrap Monte Carlo noise floor. Percentile CIs would suffice for recsys; BCa "
    "is reported for completeness and procedural consistency with markets."
)
lines.append("")
lines.append(
    "- **Markets BCa correction is substantive for the p witness.** The Glass's d markets "
    "p cell upper bound shifts from percentile +1.357 to BCa +2.094 (54% right-shift). "
    "Bootstrap distribution is right-skewed at n=54; percentile CIs systematically "
    "understate the right tail. BCa is the honest read here."
)
lines.append("")
lines.append(
    "- **Canonical h=50 is the only configuration where all three witnesses align in "
    "the predicted direction with CIs clear of 0** (bolded above). Adjacent recsys "
    "horizons degrade asymmetrically: h=40 G flips sign while p and \u03b4 hold; h=60 G "
    "strengthens while p and \u03b4 collapse to null. The pre-registered horizon delivers "
    "the cleanest signature \u2014 evidence that pre-registration was load-bearing for the bridge claim."
)
lines.append("")
lines.append(
    "- **Markets row-level effects are uniformly null** (all three witnesses, all three "
    "measures, all CIs span 0 or 0.5). The directional bridge claim for markets operates "
    "at unit-level aggregation grain (mean per unit, then compare unit means across the "
    "n=38+16 segments); the row-level effect-size table above is honest data at the finer "
    "grain. See main text Cross-domain evidence section for the unit-level framing."
)
lines.append("")
lines.append("---")
lines.append("")
lines.append(
    "**See also:** Figure [N] (effect-size forest plot, results/figures/a3_effect_size_forest.{png,pdf}); "
    "Cross-domain evidence section of the main manuscript."
)
lines.append("")

OUT_PATH.write_text("\n".join(lines))
print(f"Wrote: {OUT_PATH}")
print(f"Lines: {len(lines)}")
