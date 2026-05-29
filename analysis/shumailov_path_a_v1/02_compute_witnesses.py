#!/usr/bin/env python3
"""
PathA.3: Compute G/p/delta witnesses on Shumailov 2024 secondary-analysis data.

Inputs (canonical digitized data from PathA.2):
  data/public/shumailov_secondary_data_v1/figure_1b_no_preservation_digitized.csv
  data/public/shumailov_secondary_data_v1/figure_1c_ten_pct_preservation_digitized.csv

Outputs:
  results/frozen/shumailov/shumailov_per_row_witnesses_v1.csv
  results/frozen/shumailov/shumailov_per_generation_aggregated_witnesses_v1.csv
  results/rendered/shumailov/witnesses_overview_v1.png

Witness operationalizations for this secondary analysis:

  G.1 (amplification): second-difference of mean perplexity per run
    G(r,g) = P(r,g) - 2 * P(r,g-1) + P(r,g-2)
    Captures rate-of-change of the growth rate. Undefined for g < 2.
    Predicted pattern: large-magnitude negative at the post-spike settling
    transition (gen 2), near zero during the post-collapse plateau.

  p.1 (recursive persistence / non-relaxation): per-run gap-to-cummax ratio
    gap(r,g) = P(r,g) - P_real(r),  P_real(r) := P(r,0)
    p(r,g) = gap(r,g) / max(gap(r, 0:g+1))    when cummax > 0
    p(r,g) = 0                                 when cummax == 0
    Predicted pattern: jumps to 1 at collapse onset, stays elevated
    (>= 0.5) across the trajectory = non-relaxation.

  delta.1 (diversity proxy): inverse cross-run standard deviation of P
    delta(g, regime) = 1 / std_runs(P(:, g))
    LIMITATION: this measures inter-seed convergence of per-generation
    perplexity, NOT within-model output-distribution diversity. The
    direct distributional-diversity measurement lives in Fig 1b/1c LEFT
    panels (perplexity histograms), which are not digitized in this v1.
    The pattern here is "consistency of trajectory across seeds": high
    delta = all seeds produce similar perplexity, low delta = seeds
    diverge.

Source data: Shumailov et al. 2024, Nature, doi:10.1038/s41586-024-07566-y
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "public" / "shumailov_secondary_data_v1"
FROZEN_DIR = REPO_ROOT / "results" / "frozen" / "shumailov"
RENDERED_DIR = REPO_ROOT / "results" / "rendered" / "shumailov"

FROZEN_DIR.mkdir(parents=True, exist_ok=True)
RENDERED_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# Load
# ------------------------------------------------------------------
def load_regime(filename: str, regime_label: str) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / filename)
    df["regime"] = regime_label
    return df


df_b = load_regime("figure_1b_no_preservation_digitized.csv", "no_preservation")
df_c = load_regime("figure_1c_ten_pct_preservation_digitized.csv", "ten_pct_preservation")
df = pd.concat([df_b, df_c], ignore_index=True)
df = df.sort_values(["regime", "run", "generation"]).reset_index(drop=True)

# Per-run baseline (generation 0 = Real wikitext2 perplexity)
df["baseline"] = df.groupby(["regime", "run"])["mean_perplexity"].transform("first")
df["gap"] = df["mean_perplexity"] - df["baseline"]

print(
    f"Loaded {len(df)} rows: {len(df_b)} no-preservation + {len(df_c)} 10%-preservation"
)
print(
    f"Baselines range: {df['baseline'].min():.3f} to {df['baseline'].max():.3f}"
)
print()


# ------------------------------------------------------------------
# Witness G.1: signed second difference of mean perplexity per run
# ------------------------------------------------------------------
df["G_amplification"] = (
    df.groupby(["regime", "run"])["mean_perplexity"]
    .transform(lambda s: s - 2 * s.shift(1) + s.shift(2))
)


# ------------------------------------------------------------------
# Witness p.1: per-run gap-to-cumulative-max ratio
# ------------------------------------------------------------------
def _gap_to_cummax_ratio(s: pd.Series) -> pd.Series:
    """gap(r,g) / cummax(gap(r, 0:g+1)); returns 0 where cummax == 0."""
    g = s.values
    cummax = np.maximum.accumulate(np.maximum(g, 0))
    safe = np.where(cummax > 0, cummax, 1.0)
    ratio = np.where(cummax > 0, g / safe, 0.0)
    return pd.Series(ratio, index=s.index)


df["p_persistence"] = (
    df.groupby(["regime", "run"])["gap"].transform(_gap_to_cummax_ratio)
)


# ------------------------------------------------------------------
# Witness delta.1: inverse cross-run perplexity std at each generation
# ------------------------------------------------------------------
df["cross_run_std"] = (
    df.groupby(["regime", "generation"])["mean_perplexity"].transform("std")
)
df["delta_diversity"] = 1.0 / df["cross_run_std"].clip(lower=1e-9)


# ------------------------------------------------------------------
# Save per-row table
# ------------------------------------------------------------------
per_row_path = FROZEN_DIR / "shumailov_per_row_witnesses_v1.csv"
df.to_csv(per_row_path, index=False)
print(f"Wrote {per_row_path.relative_to(REPO_ROOT)}")


# ------------------------------------------------------------------
# Aggregate across runs (mean witnesses per regime x generation)
# ------------------------------------------------------------------
agg = (
    df.groupby(["regime", "generation"], as_index=False)
    .agg(
        mean_perplexity_mean=("mean_perplexity", "mean"),
        mean_perplexity_std=("mean_perplexity", "std"),
        gap_mean=("gap", "mean"),
        G_amplification_mean=("G_amplification", "mean"),
        p_persistence_mean=("p_persistence", "mean"),
        delta_diversity=("delta_diversity", "first"),
        cross_run_std=("cross_run_std", "first"),
    )
)

agg_path = FROZEN_DIR / "shumailov_per_generation_aggregated_witnesses_v1.csv"
agg.to_csv(agg_path, index=False)
print(f"Wrote {agg_path.relative_to(REPO_ROOT)}")
print()


# ------------------------------------------------------------------
# Plot: 4-panel overview
# ------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
fig.suptitle(
    "Shumailov 2024 secondary analysis: G/p/delta witnesses\n"
    "(cross-run means over 5 seeds x 10 generations)",
    fontsize=11,
)

regimes = [
    ("no_preservation", "No preservation (Fig 1b)", "C0", "-"),
    ("ten_pct_preservation", "10% preservation (Fig 1c)", "C1", "--"),
]

# Panel (a): mean perplexity (sanity check)
ax = axes[0, 0]
for regime, label, color, ls in regimes:
    sub = agg[agg.regime == regime]
    ax.plot(sub.generation, sub.mean_perplexity_mean, ls, color=color,
            marker="o", label=label)
    ax.fill_between(
        sub.generation,
        sub.mean_perplexity_mean - sub.mean_perplexity_std,
        sub.mean_perplexity_mean + sub.mean_perplexity_std,
        alpha=0.15, color=color,
    )
ax.set_xlabel("Generation")
ax.set_ylabel("Mean perplexity")
ax.set_title("(a) Mean perplexity (sanity check)")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# Panel (b): G.1
ax = axes[0, 1]
for regime, label, color, ls in regimes:
    sub = agg[agg.regime == regime]
    ax.plot(sub.generation, sub.G_amplification_mean, ls, color=color,
            marker="o", label=label)
ax.axhline(0, color="black", linewidth=0.5, alpha=0.5)
ax.set_xlabel("Generation")
ax.set_ylabel("G.1 = second difference of P")
ax.set_title("(b) G.1 amplification")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# Panel (c): p.1
ax = axes[1, 0]
for regime, label, color, ls in regimes:
    sub = agg[agg.regime == regime]
    ax.plot(sub.generation, sub.p_persistence_mean, ls, color=color,
            marker="o", label=label)
ax.set_xlabel("Generation")
ax.set_ylabel("p.1 = gap / cumulative-max-gap")
ax.set_title("(c) p.1 recursive persistence")
ax.set_ylim(-0.05, 1.1)
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# Panel (d): delta.1
ax = axes[1, 1]
for regime, label, color, ls in regimes:
    sub = agg[agg.regime == regime]
    ax.plot(sub.generation, sub.delta_diversity, ls, color=color,
            marker="o", label=label)
ax.set_xlabel("Generation")
ax.set_ylabel("delta.1 = 1 / cross-run std(P)")
ax.set_title("(d) delta.1 diversity proxy (log scale)")
ax.set_yscale("log")
ax.legend(fontsize=8)
ax.grid(alpha=0.3, which="both")

plt.tight_layout()
plot_path = RENDERED_DIR / "witnesses_overview_v1.png"
plt.savefig(plot_path, dpi=150, bbox_inches="tight")
print(f"Wrote {plot_path.relative_to(REPO_ROOT)}")
print()


# ------------------------------------------------------------------
# Print summary table
# ------------------------------------------------------------------
print("=" * 90)
print("Per-generation aggregated witnesses")
print("=" * 90)

display_cols = [
    "regime", "generation",
    "mean_perplexity_mean",
    "G_amplification_mean",
    "p_persistence_mean",
    "delta_diversity",
]
display_df = agg[display_cols].copy()
for col in ["mean_perplexity_mean", "G_amplification_mean",
            "p_persistence_mean", "delta_diversity"]:
    display_df[col] = display_df[col].round(3)
print(display_df.to_string(index=False))
print()
print("Done.")
