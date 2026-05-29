#!/usr/bin/env python3
"""
analysis/15_compute_effect_sizes.py

A3 — effect sizes, confidence intervals, bootstrap uncertainty.

Companion to:
  analysis/14_build_a1_quantile_detector_v1.py  (canonical A1 detector)
  analysis/14b_a1_recsys_horizon_variants.py    (recsys h40/h60 wrapper)

Computes per-witness (G, p, δ) effect-size measures with bootstrap 95% CIs
for each benchmark/horizon combination, addressing the v1.0 adversarial-
review item A3 (effect sizes, CIs, bootstrap uncertainty).

Scope: 4 benchmark/horizon targets × 3 witnesses × 3 effect measures
= 36 estimates, each with a 95% CI = 108 numerical values for the
Supplementary Table S2 the manuscript references.

Sprint brief: https://www.notion.so/3652f04eb69181ac8505cfdaf80788a8

# Pre-locked design decisions (DO NOT re-litigate; see sprint brief for rationale)

## Bootstrap unit
- markets: segment-level (preserves intra-event clustering around Volmageddon
  and March 2020 MWCB; n=38 controls + 16 events at segment grain)
- recsys (all three horizons): user-level (40,339 user clusters; respects
  user-level independence; same partition as canonical h=50 and the h=40 /
  h=60 robustness packets, all three byte-exact reproducible against May 8
  baseline anchors verified Tue May 19)

## Bootstrap iterations
- 10,000 iterations (publication-grade CIs)
- Checkpoint every 1,000 iterations to allow resume on interruption.
  Checkpoint contents: partial bootstrap distribution as .npy, plus a
  metadata JSON with iteration count, random-state seed, and elapsed time.

## CI method
- Primary: percentile bootstrap (95% CI = 2.5th and 97.5th percentiles of
  the bootstrap distribution). Simpler; no normality assumption.
- Sensitivity: BCa bootstrap (bias-corrected accelerated). Reported alongside
  percentile in Supplementary Table S2 as a robustness check.

## Effect-size measures
- Cohen's d (pooled SD) — primary headline reporting
- Glass's d (control SD only) — important for n-asymmetric comparisons
  (e.g., n_control=4,755 vs n_event=35,584 on recsys h=50 canonical)
- Rank AUC — non-parametric, robust to outliers, complements parametric d's;
  computed via Mann-Whitney U statistic / (n_event × n_control)

## Reference rows (event-row / control-row selection)
- markets: per-row ingredient-packet rows from the last 30 min of each
  canonical unit window (same selection convention as
  analysis/14:select_reference_rows). Event rows = pre-collapse rows within
  event-unit windows; control rows = same window within control-unit windows.
- recsys (all horizons): control-unit per-step rows inside the pre-collapse
  panel (same selection as analysis/14:select_reference_rows). Event rows =
  pre-collapse event-unit per-step rows.

## NaN handling
- Rows with any NaN in (G, p, δ) are dropped before effect-size computation,
  consistent with pre-reg §4 of the A1 detector.

## Random seed
- numpy.random.default_rng(RANDOM_SEED=42) for top-level bootstrap
  reproducibility.
- Child generators spawned per (benchmark, horizon, witness, measure)
  combination via numpy.random.SeedSequence.spawn() for reproducible
  per-combination streams independent of execution order or parallelism.

# Inputs
  results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/
    cfg_001339__*.packet.csv  (markets per-row panel)
  results/manifests/movielens25m_recursive_frontier_public_v1__telemetry_panel.csv.gz
    (recsys canonical h=50 per-step panel)
  results/robustness/recommender/movielens25m_recursive_frontier_public_v1__horizon_40_packet/
    results/manifests/...__telemetry_panel.csv.gz (recsys h=40 per-step panel)
  results/robustness/recommender/movielens25m_recursive_frontier_public_v1__horizon_60_packet/
    results/manifests/...__telemetry_panel.csv.gz (recsys h=60 per-step panel)

# Outputs
  results/rendered/effect_sizes/a3_effect_sizes_full.csv
    (Supplementary Table S2: 36 rows × point+CI columns)
  results/rendered/effect_sizes/a3_effect_sizes_summary.md
    (paper-facing condensed summary for prose integration)
  results/rendered/effect_sizes/a3_bootstrap_checkpoints/
    (per-1K-iteration checkpoints, npy + json)

# Status
Day 1 — scaffolding only. Function bodies stubbed; bodies land in Day 2.
"""

from __future__ import annotations

import argparse
import importlib
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, norm

# Ensure repo root is on sys.path so 'analysis' is importable when this script
# is run directly (otherwise sys.path[0] becomes the analysis/ dir, not the
# repo root, and the 'analysis' package import fails).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Reuse canonical detector + recsys horizon wrapper loaders via importlib
# (digit-prefixed module names cannot be imported directly).
_a1 = importlib.import_module("analysis.14_build_a1_quantile_detector_v1")
_a1h = importlib.import_module("analysis.14b_a1_recsys_horizon_variants")

# ---------------------------------------------------------------------------
# Constants (design decisions locked in module docstring above)
# ---------------------------------------------------------------------------
BOOTSTRAP_ITERATIONS: int = 10_000
CHECKPOINT_INTERVAL: int = 1_000
CI_LEVEL: float = 0.95
RANDOM_SEED: int = 42

EFFECT_MEASURES: tuple[str, ...] = ("cohens_d", "glasss_d", "rank_auc")
WITNESSES: tuple[str, ...] = ("G", "p", "delta")

CIMethod = Literal["percentile", "bca"]
CI_METHOD_PRIMARY: CIMethod = "percentile"
CI_METHOD_SENSITIVITY: CIMethod = "bca"

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
OUT_DIR: Path = REPO_ROOT / "results" / "rendered" / "effect_sizes"
OUT_CSV: Path = OUT_DIR / "a3_effect_sizes_full.csv"
OUT_MD: Path = OUT_DIR / "a3_effect_sizes_summary.md"
CHECKPOINT_DIR: Path = OUT_DIR / "a3_bootstrap_checkpoints"


# ---------------------------------------------------------------------------
# Benchmark / horizon target specifications
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class BenchmarkSpec:
    """One (benchmark, horizon) target for effect-size computation."""
    benchmark_id: str
    domain: Literal["markets", "recsys"]
    horizon: int | None  # None for markets; 40, 50, or 60 for recsys
    panel_path: Path
    bootstrap_unit_col: str


# 4-target spec list. Recsys paths anchored to packets verified byte-exact
# reproducible against May 8 baseline (h40 b7a8cae1..., h50 daa7b8fa...,
# h60 b59a54d1...) on Tue May 19.
BENCHMARK_SPECS: tuple[BenchmarkSpec, ...] = (
    BenchmarkSpec(
        benchmark_id="volmageddon_covid_public_v2",
        domain="markets",
        horizon=None,
        panel_path=REPO_ROOT
        / "results"
        / "rendered"
        / "equity_dislocation_family"
        / "intraday_v2_ingredient_packet",
        bootstrap_unit_col="unit_id",
    ),
    BenchmarkSpec(
        benchmark_id="movielens25m_recursive_frontier_public_v1__horizon_40",
        domain="recsys",
        horizon=40,
        panel_path=REPO_ROOT
        / "results"
        / "robustness"
        / "recommender"
        / "movielens25m_recursive_frontier_public_v1__horizon_40_packet"
        / "results"
        / "manifests"
        / "movielens25m_recursive_frontier_public_v1__telemetry_panel.csv.gz",
        bootstrap_unit_col="unit_id",
    ),
    BenchmarkSpec(
        benchmark_id="movielens25m_recursive_frontier_public_v1__canonical_h50",
        domain="recsys",
        horizon=50,
        panel_path=REPO_ROOT
        / "results"
        / "manifests"
        / "movielens25m_recursive_frontier_public_v1__telemetry_panel.csv.gz",
        bootstrap_unit_col="unit_id",
    ),
    BenchmarkSpec(
        benchmark_id="movielens25m_recursive_frontier_public_v1__horizon_60",
        domain="recsys",
        horizon=60,
        panel_path=REPO_ROOT
        / "results"
        / "robustness"
        / "recommender"
        / "movielens25m_recursive_frontier_public_v1__horizon_60_packet"
        / "results"
        / "manifests"
        / "movielens25m_recursive_frontier_public_v1__telemetry_panel.csv.gz",
        bootstrap_unit_col="unit_id",
    ),
)


# ---------------------------------------------------------------------------
# Effect-size functions (Day 2 implementation)
# ---------------------------------------------------------------------------
def compute_cohens_d(
    event_values: np.ndarray,
    control_values: np.ndarray,
) -> float:
    """Cohen's d (pooled SD) for two samples.

    d = (mean_event - mean_control) / sd_pooled
    sd_pooled = sqrt(((n_e - 1) * sd_e^2 + (n_c - 1) * sd_c^2) / (n_e + n_c - 2))

    Returns NaN if either sample has fewer than 2 elements or sd_pooled == 0.

    Parameters
    ----------
    event_values : np.ndarray, shape (n_event,)
        Per-row witness values for event units (NaN-free).
    control_values : np.ndarray, shape (n_control,)
        Per-row witness values for control units (NaN-free).

    Returns
    -------
    float
        Cohen's d. Sign convention: positive => event mean > control mean.
    """
    n_e = event_values.shape[0]
    n_c = control_values.shape[0]
    if n_e < 2 or n_c < 2:
        return float("nan")
    mean_e = float(np.mean(event_values))
    mean_c = float(np.mean(control_values))
    var_e = float(np.var(event_values, ddof=1))
    var_c = float(np.var(control_values, ddof=1))
    pooled_var = ((n_e - 1) * var_e + (n_c - 1) * var_c) / (n_e + n_c - 2)
    sd_pooled = float(np.sqrt(pooled_var))
    if sd_pooled == 0.0:
        return float("nan")
    return (mean_e - mean_c) / sd_pooled


def compute_glasss_d(
    event_values: np.ndarray,
    control_values: np.ndarray,
) -> float:
    """Glass's d (control-SD-only) for two samples.

    d = (mean_event - mean_control) / sd_control

    Robust to n-asymmetric comparisons (recsys: n_control ≪ n_event), where
    pooled SD is dominated by the larger sample and may underestimate the
    practical effect against the smaller control distribution.

    Returns NaN if control sample has fewer than 2 elements or sd_control == 0,
    or if event sample is empty.

    Parameters
    ----------
    event_values : np.ndarray, shape (n_event,)
    control_values : np.ndarray, shape (n_control,)

    Returns
    -------
    float
        Glass's d. Sign convention: positive => event mean > control mean.
    """
    n_e = event_values.shape[0]
    n_c = control_values.shape[0]
    if n_e == 0 or n_c < 2:
        return float("nan")
    mean_e = float(np.mean(event_values))
    mean_c = float(np.mean(control_values))
    sd_c = float(np.std(control_values, ddof=1))
    if sd_c == 0.0:
        return float("nan")
    return (mean_e - mean_c) / sd_c


def compute_rank_auc(
    event_values: np.ndarray,
    control_values: np.ndarray,
) -> float:
    """Rank AUC = P(event-row value > control-row value), with ties at 0.5.

    Non-parametric; equivalent to AUC of the optimal monotone classifier on
    the witness. AUC = 0.5 → no separation; AUC = 1.0 → perfect separation in
    event > control direction; AUC = 0.0 → perfect separation in event < control
    direction (used for the δ witness, where the predicted direction is
    event < control because event δ is contracted).

    Uses scipy.stats.mannwhitneyu with alternative="greater" to get the U
    statistic = #{(e, c) pairs with e > c} + 0.5 * #ties directly, so
    AUC = U / (n_event * n_control) is sign-correct.

    Returns NaN if either sample is empty.

    Parameters
    ----------
    event_values : np.ndarray, shape (n_event,)
    control_values : np.ndarray, shape (n_control,)

    Returns
    -------
    float
        Rank AUC ∈ [0, 1].
    """
    n_e = event_values.shape[0]
    n_c = control_values.shape[0]
    if n_e == 0 or n_c == 0:
        return float("nan")
    result = mannwhitneyu(event_values, control_values, alternative="greater")
    return float(result.statistic / (n_e * n_c))


# ---------------------------------------------------------------------------
# Cluster-aware bootstrap CI (Day 2 implementation)
# ---------------------------------------------------------------------------
def _pregroup_for_bootstrap(
    rows: pd.DataFrame,
    witness_col: str,
    unit_col: str,
):
    """Pre-group rows by unit_col for fast cluster-aware bootstrap resampling.

    Returns (data, sizes, n_units) where:
    - data is a 2D numpy array of shape (n_units, group_size) when all groups
      have the same size (recsys: exactly 10 rows per unit), enabling fast
      fancy-indexing + ravel in the bootstrap loop.
    - data is a list of 1D numpy arrays in unit-iteration order when groups
      have variable sizes (markets: ~30 rows per unit, slight variation),
      requiring list-comp + np.concatenate per iteration.
    - sizes is None in the uniform case, else a 1D array of group sizes.
    - n_units is the number of distinct units.
    """
    groups = [grp[witness_col].to_numpy()
              for _, grp in rows.groupby(unit_col, sort=False)]
    n_units = len(groups)
    if n_units == 0:
        return np.array([]), None, 0
    sizes = np.array([len(g) for g in groups])
    if (sizes == sizes[0]).all():
        return np.stack(groups), None, n_units
    return groups, sizes, n_units


def _resample_clustered(
    data,
    sizes,
    n_units: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample n_units unit-indices WITH REPLACEMENT and return concatenated
    witness values. Fast 2D path for uniform-size case; list-comp fallback
    for variable-size case."""
    boot_idx = rng.integers(0, n_units, size=n_units)
    if sizes is None:
        return data[boot_idx].ravel()
    return np.concatenate([data[i] for i in boot_idx])


def bootstrap_ci(
    event_rows: pd.DataFrame,
    control_rows: pd.DataFrame,
    witness_col: str,
    unit_col: str,
    statistic_fn: Callable[[np.ndarray, np.ndarray], float],
    *,
    n_iterations: int = BOOTSTRAP_ITERATIONS,
    checkpoint_interval: int = CHECKPOINT_INTERVAL,
    checkpoint_path: Path | None = None,
    rng: np.random.Generator | None = None,
    method: CIMethod = CI_METHOD_PRIMARY,
) -> tuple[float, float, float, np.ndarray]:
    """Cluster-aware bootstrap CI for a 2-sample statistic.

    Resamples WITH REPLACEMENT at the unit_col level (preserves intra-unit
    dependence — critical for markets event clustering and recsys per-user
    multi-step rows). Computes statistic_fn(event_values, control_values) on
    each bootstrap sample.

    Checkpoint protocol: every checkpoint_interval iterations, writes the
    partial bootstrap distribution as .npy and a metadata JSON
    (iteration_count, seed, elapsed_time) to checkpoint_path. Allows resume
    on interruption (Day 3 implementation; not in Day 2 minimal pass).

    Parameters
    ----------
    event_rows : pd.DataFrame
        Per-row event panel; must contain unit_col and witness_col.
    control_rows : pd.DataFrame
        Per-row control panel; must contain unit_col and witness_col.
    witness_col : str
        Column name of the witness (one of "G", "p", "delta").
    unit_col : str
        Column name of the bootstrap unit (segment for markets, user for recsys).
    statistic_fn : Callable[[np.ndarray, np.ndarray], float]
        One of compute_cohens_d, compute_glasss_d, compute_rank_auc.
    n_iterations : int
        Number of bootstrap iterations (default BOOTSTRAP_ITERATIONS).
    checkpoint_interval : int
        Write checkpoint every N iterations.
    checkpoint_path : Path | None
        If provided, checkpoints written here.
    rng : np.random.Generator | None
        Bootstrap RNG. If None, seeded from RANDOM_SEED.
    method : "percentile" or "bca"
        CI computation method. Percentile is primary; BCa is sensitivity check.

    Returns
    -------
    point_estimate : float
        statistic_fn evaluated on the original (un-resampled) data.
    ci_lower : float
        Lower CI bound at (1 - CI_LEVEL) / 2 percentile of bootstrap distribution.
    ci_upper : float
        Upper CI bound at 1 - (1 - CI_LEVEL) / 2 percentile.
    bootstrap_distribution : np.ndarray, shape (n_iterations,)
        Full bootstrap statistic values, retained for downstream BCa
        correction and Day 3 sensitivity diagnostics.
    """
    if rng is None:
        rng = np.random.default_rng(RANDOM_SEED)
    if method != "percentile":
        raise NotImplementedError(
            f"CI method '{method}' deferred to Day 3 (BCa); use 'percentile' for Day 2."
        )

    # Point estimate on original (un-resampled) data
    event_vals = event_rows[witness_col].to_numpy()
    control_vals = control_rows[witness_col].to_numpy()
    point_estimate = statistic_fn(event_vals, control_vals)

    # Pre-group for fast cluster-aware resampling. Uniform-size path is taken
    # automatically for recsys (10 rows/unit); variable-size path for markets.
    e_data, e_sizes, n_e = _pregroup_for_bootstrap(event_rows, witness_col, unit_col)
    c_data, c_sizes, n_c = _pregroup_for_bootstrap(control_rows, witness_col, unit_col)

    # Bootstrap loop. Checkpoint logic deferred to Day 3.
    bootstrap_dist = np.empty(n_iterations)
    for i in range(n_iterations):
        be = _resample_clustered(e_data, e_sizes, n_e, rng)
        bc = _resample_clustered(c_data, c_sizes, n_c, rng)
        bootstrap_dist[i] = statistic_fn(be, bc)

    # Percentile CI
    alpha = 1.0 - CI_LEVEL
    ci_lower = float(np.percentile(bootstrap_dist, alpha / 2.0 * 100.0))
    ci_upper = float(np.percentile(bootstrap_dist, (1.0 - alpha / 2.0) * 100.0))

    return point_estimate, ci_lower, ci_upper, bootstrap_dist


# ---------------------------------------------------------------------------
# Panel loader (Day 2 implementation)
# ---------------------------------------------------------------------------
def load_panel_for_spec(spec: BenchmarkSpec) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and partition a benchmark/horizon panel into (event_rows, control_rows).

    Reuses the canonical detector loaders directly via the _a1 and _a1h module
    references. This guarantees the event/control partition is byte-identical
    to what the A1 operating-point tables operate on — no risk of divergent
    column resolution, pre-collapse filtering, or unit-window slicing.

    Three branches:
    - markets:        _a1.load_markets_per_row_panel()
                      (uses canonical units CSV from _m13bb; last 30 min per
                      unit window; n=38 controls + 16 events)
    - recsys h50:     _a1.load_recsys_per_step_panel()
                      (hardcoded horizon=50; n=4,755 controls + 35,584 events)
    - recsys h40/h60: _a1h.load_packet_per_step_panel(packet_dir, horizon)
                      (parameterized loader from the A1 wrapper script)

    Parameters
    ----------
    spec : BenchmarkSpec

    Returns
    -------
    event_rows : pd.DataFrame
        Per-row event panel. Columns include unit_id, kind, G, p, delta (plus
        ts for markets / step for recsys); NaN rows in (G, p, delta) already
        dropped by the upstream loader.
    control_rows : pd.DataFrame
        Same columns; control units only.
    """
    if spec.domain == "markets":
        panel = _a1.load_markets_per_row_panel()
    elif spec.horizon == 50:
        panel = _a1.load_recsys_per_step_panel()
    else:
        # Recsys h=40 or h=60. spec.panel_path points to
        # .../<packet_dir>/results/manifests/telemetry_panel.csv.gz
        # The 14b loader expects the packet root directory (3 levels up).
        packet_dir = spec.panel_path.parent.parent.parent
        panel = _a1h.load_packet_per_step_panel(packet_dir, spec.horizon)

    event_rows = panel.loc[panel["kind"] == "event"].copy().reset_index(drop=True)
    control_rows = panel.loc[panel["kind"] == "control"].copy().reset_index(drop=True)
    return event_rows, control_rows


# ---------------------------------------------------------------------------
# Output formatters (Day 2 implementation)
# ---------------------------------------------------------------------------

# ============================================================================
# Jackknife (leave-one-cluster-out) for BCa acceleration
# ============================================================================
# Cohens d and Glasss d use running-sums decomposition;
# Rank AUC uses U-statistic decomposition via searchsorted.
# Returns 1D array in order:
#   [leave-event-cluster-0 ... leave-event-cluster-{n_e-1},
#    leave-control-cluster-0 ... leave-control-cluster-{n_c-1}]


def _cluster_sums(values: np.ndarray, units: np.ndarray):
    """Group values by units and return per-cluster (sum, sum_sq, count) plus globals."""
    unique_units, inv = np.unique(units, return_inverse=True)
    cluster_sum = np.bincount(inv, weights=values)
    cluster_sum_sq = np.bincount(inv, weights=values ** 2)
    cluster_n = np.bincount(inv).astype(np.int64)
    return (
        unique_units, cluster_sum, cluster_sum_sq, cluster_n,
        float(values.sum()), float((values ** 2).sum()), len(values),
    )


def _cohens_d_from_sums(s_e, ssq_e, n_e, s_c, ssq_c, n_c) -> float:
    if n_e < 2 or n_c < 2:
        return float("nan")
    mean_e = s_e / n_e
    mean_c = s_c / n_c
    var_e = max((ssq_e - n_e * mean_e * mean_e) / (n_e - 1), 0.0)
    var_c = max((ssq_c - n_c * mean_c * mean_c) / (n_c - 1), 0.0)
    pooled = ((n_e - 1) * var_e + (n_c - 1) * var_c) / (n_e + n_c - 2)
    if pooled <= 0:
        return 0.0
    return float((mean_e - mean_c) / np.sqrt(pooled))


def _glasss_d_from_sums(s_e, n_e, s_c, ssq_c, n_c) -> float:
    if n_e < 1 or n_c < 2:
        return float("nan")
    mean_e = s_e / n_e
    mean_c = s_c / n_c
    var_c = max((ssq_c - n_c * mean_c * mean_c) / (n_c - 1), 0.0)
    if var_c <= 0:
        return 0.0
    return float((mean_e - mean_c) / np.sqrt(var_c))


def _jackknife_d_family(
    event_rows: pd.DataFrame,
    control_rows: pd.DataFrame,
    witness_col: str,
    unit_col: str,
    d_type: str,
) -> np.ndarray:
    """O(n_clusters) jackknife for Cohens d (d_type=cohens) or Glasss d."""
    e_df = event_rows[[witness_col, unit_col]].dropna(subset=[witness_col])
    c_df = control_rows[[witness_col, unit_col]].dropna(subset=[witness_col])
    e_vals = e_df[witness_col].to_numpy(); e_units = e_df[unit_col].to_numpy()
    c_vals = c_df[witness_col].to_numpy(); c_units = c_df[unit_col].to_numpy()

    (u_e, cs_e, css_e, cn_e, S_e, SSQ_e, N_e) = _cluster_sums(e_vals, e_units)
    (u_c, cs_c, css_c, cn_c, S_c, SSQ_c, N_c) = _cluster_sums(c_vals, c_units)

    jack_e = np.empty(len(u_e)); jack_c = np.empty(len(u_c))

    if d_type == "cohens":
        for k in range(len(u_e)):
            jack_e[k] = _cohens_d_from_sums(
                S_e - cs_e[k], SSQ_e - css_e[k], N_e - cn_e[k], S_c, SSQ_c, N_c
            )
        for k in range(len(u_c)):
            jack_c[k] = _cohens_d_from_sums(
                S_e, SSQ_e, N_e, S_c - cs_c[k], SSQ_c - css_c[k], N_c - cn_c[k]
            )
    elif d_type == "glasss":
        for k in range(len(u_e)):
            jack_e[k] = _glasss_d_from_sums(
                S_e - cs_e[k], N_e - cn_e[k], S_c, SSQ_c, N_c
            )
        for k in range(len(u_c)):
            jack_c[k] = _glasss_d_from_sums(
                S_e, N_e, S_c - cs_c[k], SSQ_c - css_c[k], N_c - cn_c[k]
            )
    else:
        raise ValueError(f"d_type must be cohens or glasss; got {d_type!r}")

    return np.concatenate([jack_e, jack_c])


def _jackknife_rank_auc(
    event_rows: pd.DataFrame,
    control_rows: pd.DataFrame,
    witness_col: str,
    unit_col: str,
) -> np.ndarray:
    """O(n_clusters) jackknife for Rank AUC via U-statistic decomposition."""
    e_df = event_rows[[witness_col, unit_col]].dropna(subset=[witness_col])
    c_df = control_rows[[witness_col, unit_col]].dropna(subset=[witness_col])
    e_vals = e_df[witness_col].to_numpy(); e_units = e_df[unit_col].to_numpy()
    c_vals = c_df[witness_col].to_numpy(); c_units = c_df[unit_col].to_numpy()
    n_e, n_c = len(e_vals), len(c_vals)
    if n_e == 0 or n_c == 0:
        return np.array([float("nan")])

    c_sorted = np.sort(c_vals)
    below_e = np.searchsorted(c_sorted, e_vals, side="left")
    not_above_e = np.searchsorted(c_sorted, e_vals, side="right")
    u_i = below_e + 0.5 * (not_above_e - below_e)

    e_sorted = np.sort(e_vals)
    above_c = n_e - np.searchsorted(e_sorted, c_vals, side="right")
    not_below_c = n_e - np.searchsorted(e_sorted, c_vals, side="left")
    v_j = above_c + 0.5 * (not_below_c - above_c)

    U_total = float(u_i.sum())
    assert abs(U_total - float(v_j.sum())) < 1e-6 * max(1.0, U_total), "u_i/v_j totals disagree"

    _, e_inv = np.unique(e_units, return_inverse=True)
    cluster_u_sum = np.bincount(e_inv, weights=u_i)
    cluster_e_n = np.bincount(e_inv).astype(np.int64)

    _, c_inv = np.unique(c_units, return_inverse=True)
    cluster_v_sum = np.bincount(c_inv, weights=v_j)
    cluster_c_n = np.bincount(c_inv).astype(np.int64)

    jack_e = (U_total - cluster_u_sum) / ((n_e - cluster_e_n) * n_c)
    jack_c = (U_total - cluster_v_sum) / (n_e * (n_c - cluster_c_n))
    return np.concatenate([jack_e, jack_c])


def jackknife_clustered(
    event_rows: pd.DataFrame,
    control_rows: pd.DataFrame,
    witness_col: str,
    unit_col: str,
    statistic_fn,
) -> np.ndarray:
    """Leave-one-cluster-out jackknife dispatched to optimized O(n_clusters) paths."""
    if statistic_fn is compute_cohens_d:
        return _jackknife_d_family(event_rows, control_rows, witness_col, unit_col, "cohens")
    if statistic_fn is compute_glasss_d:
        return _jackknife_d_family(event_rows, control_rows, witness_col, unit_col, "glasss")
    if statistic_fn is compute_rank_auc:
        return _jackknife_rank_auc(event_rows, control_rows, witness_col, unit_col)
    raise NotImplementedError(
        f"No optimized jackknife for statistic_fn={statistic_fn!r}"
    )


# ============================================================================
# BCa correction from bootstrap distribution + jackknife estimates
# ============================================================================


def compute_bca_correction(
    point_estimate: float,
    bootstrap_distribution: np.ndarray,
    jackknife_estimates: np.ndarray,
    ci_level: float = CI_LEVEL,
) -> tuple[float, float]:
    """Efron (1987) BCa interval endpoints from bootstrap distribution + jackknife."""
    jack = jackknife_estimates[~np.isnan(jackknife_estimates)]
    if len(jack) < 2:
        return float("nan"), float("nan")

    alpha = 1.0 - ci_level

    prop_below = float(np.mean(bootstrap_distribution < point_estimate))
    prop_below = float(np.clip(prop_below, 1e-10, 1 - 1e-10))
    z0 = float(norm.ppf(prop_below))

    jack_mean = float(jack.mean())
    diff = jack_mean - jack
    sum_sq = float((diff ** 2).sum())
    a = 0.0 if sum_sq <= 0 else float((diff ** 3).sum() / (6.0 * sum_sq ** 1.5))

    z_lo = float(norm.ppf(alpha / 2.0))
    z_hi = float(norm.ppf(1.0 - alpha / 2.0))

    def _adjust(z):
        denom = 1.0 - a * (z0 + z)
        if denom == 0:
            denom = 1e-12
        return float(norm.cdf(z0 + (z0 + z) / denom)) * 100.0

    pct_lo = float(np.clip(_adjust(z_lo), 0.0, 100.0))
    pct_hi = float(np.clip(_adjust(z_hi), 0.0, 100.0))
    return (
        float(np.percentile(bootstrap_distribution, pct_lo)),
        float(np.percentile(bootstrap_distribution, pct_hi)),
    )


def build_supplementary_table_s2(rows: list[dict]) -> pd.DataFrame:
    """Build Supplementary Table S2 DataFrame from per-cell result rows.

    Each row = one (benchmark_id, horizon, witness, effect_measure) tuple.
    Day 2 minimal pass: column order set, BCa columns NaN (Day 3 deferred).
    """
    column_order = [
        "benchmark_id", "domain", "horizon",
        "witness", "effect_measure",
        "n_event_units", "n_control_units",
        "n_event_rows", "n_control_rows",
        "point_estimate",
        "ci_lower_percentile", "ci_upper_percentile",
        "ci_lower_bca", "ci_upper_bca",
        "n_iterations",
    ]
    df = pd.DataFrame(rows)
    # Reorder + fill any missing columns with NaN
    for c in column_order:
        if c not in df.columns:
            df[c] = float("nan")
    return df[column_order]


def write_outputs(
    table: pd.DataFrame,
    csv_path: Path,
    md_path: Path,
) -> None:
    """Write Supplementary Table S2 CSV + paper-facing summary MD.

    Day 2 minimal pass: CSV is the full table; MD is a simple flat rendering
    grouped by benchmark. Day 4 will polish: bolding manuscript-relevant
    primary cells, adding cross-references to bridge-result narrative.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(csv_path, index=False)

    lines: list[str] = [
        "# A3 — Effect sizes & bootstrap 95% CIs",
        "",
        "Per-row Cohen's d, Glass's d, and Rank AUC with cluster-aware bootstrap "
        "95% percentile CIs.",
        "",
        "Bootstrap unit grain:",
        "- markets: segment-level (n=38 controls + 16 events)",
        "- recsys (all horizons): user-level (40,339 user clusters; ~10 rows/unit)",
        "",
        f"Bootstrap iterations: {int(table['n_iterations'].iloc[0])} per cell. "
        "BCa CI computation deferred to Day 3.",
        "",
        "Sign convention: Cohen's d > 0 and AUC > 0.5 => event mean > control mean. "
        "For the δ witness, predicted direction is event < control (δ contracted in "
        "events), so d < 0 and AUC < 0.5 are the expected directions.",
        "",
        "| Benchmark | Witness | Measure | Point | 95% CI lower | 95% CI upper |",
        "|---|---|---|---:|---:|---:|",
    ]
    for _, r in table.iterrows():
        lines.append(
            f"| {r['benchmark_id']} | {r['witness']} | {r['effect_measure']} "
            f"| {r['point_estimate']:.4f} "
            f"| {r['ci_lower_percentile']:.4f} "
            f"| {r['ci_upper_percentile']:.4f} |"
        )
    md_path.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--n-iterations",
        type=int,
        default=BOOTSTRAP_ITERATIONS,
        help=f"Bootstrap iterations (default: {BOOTSTRAP_ITERATIONS}).",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=CHECKPOINT_INTERVAL,
        help=f"Checkpoint every N iterations (default: {CHECKPOINT_INTERVAL}).",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=OUT_CSV,
        help=f"Output CSV path (default: {OUT_CSV}).",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=OUT_MD,
        help=f"Output Markdown path (default: {OUT_MD}).",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=CHECKPOINT_DIR,
        help=f"Bootstrap checkpoint directory (default: {CHECKPOINT_DIR}).",
    )
    parser.add_argument(
        "--skip-bca",
        action="store_true",
        help="Skip BCa CI sensitivity computation (percentile only).",
    )
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Restrict to a single benchmark_id (testing/debugging).",
    )
    args = parser.parse_args(argv)

    # Map measure name to statistic function
    statistic_fns: dict[str, Callable[[np.ndarray, np.ndarray], float]] = {
        "cohens_d": compute_cohens_d,
        "glasss_d": compute_glasss_d,
        "rank_auc": compute_rank_auc,
    }

    # Filter specs if --only requested
    specs_to_run = list(BENCHMARK_SPECS)
    if args.only is not None:
        specs_to_run = [s for s in specs_to_run if s.benchmark_id == args.only]
        if not specs_to_run:
            raise ValueError(
                f"No BenchmarkSpec matches --only={args.only!r}; "
                f"valid IDs: {[s.benchmark_id for s in BENCHMARK_SPECS]}"
            )

    # Reproducible per-cell RNGs via SeedSequence spawning
    n_cells = len(specs_to_run) * len(WITNESSES) * len(EFFECT_MEASURES)
    seed_seq_root = np.random.SeedSequence(RANDOM_SEED)
    cell_seeds = seed_seq_root.spawn(n_cells)

    all_rows: list[dict] = []
    cell_idx = 0
    t_start = time.time()
    for spec in specs_to_run:
        print(f"\n[{spec.benchmark_id}] loading panel ...", file=sys.stderr)
        event_rows, control_rows = load_panel_for_spec(spec)
        n_event_units = int(event_rows[spec.bootstrap_unit_col].nunique())
        n_control_units = int(control_rows[spec.bootstrap_unit_col].nunique())
        n_event_rows = len(event_rows)
        n_control_rows = len(control_rows)
        print(
            f"  events:   {n_event_rows:>7} rows / {n_event_units:>5} units",
            file=sys.stderr,
        )
        print(
            f"  controls: {n_control_rows:>7} rows / {n_control_units:>5} units",
            file=sys.stderr,
        )

        for witness in WITNESSES:
            for measure in EFFECT_MEASURES:
                rng = np.random.default_rng(cell_seeds[cell_idx])
                cell_idx += 1
                t0 = time.time()
                point, lo_pct, hi_pct, bootstrap_dist = bootstrap_ci(
                    event_rows,
                    control_rows,
                    witness_col=witness,
                    unit_col=spec.bootstrap_unit_col,
                    statistic_fn=statistic_fns[measure],
                    n_iterations=args.n_iterations,
                    checkpoint_interval=args.checkpoint_interval,
                    rng=rng,
                    method="percentile",
                )
                t_boot = time.time() - t0

                t0 = time.time()
                jack = jackknife_clustered(
                    event_rows, control_rows, witness,
                    spec.bootstrap_unit_col, statistic_fns[measure],
                )
                lo_bca, hi_bca = compute_bca_correction(
                    point, bootstrap_dist, jack, ci_level=CI_LEVEL,
                )
                t_jack = time.time() - t0

                print(
                    f"  {witness:>5} / {measure:<8}: "
                    f"point={point:>+8.4f}  "
                    f"pct=[{lo_pct:>+8.4f}, {hi_pct:>+8.4f}]  "
                    f"bca=[{lo_bca:>+8.4f}, {hi_bca:>+8.4f}]  "
                    f"(boot={t_boot:>5.1f}s, jack={t_jack:>5.2f}s)",
                    file=sys.stderr,
                )

                all_rows.append({
                    "benchmark_id": spec.benchmark_id,
                    "domain": spec.domain,
                    "horizon": spec.horizon if spec.horizon is not None else "",
                    "witness": witness,
                    "effect_measure": measure,
                    "n_event_units": n_event_units,
                    "n_control_units": n_control_units,
                    "n_event_rows": n_event_rows,
                    "n_control_rows": n_control_rows,
                    "point_estimate": point,
                    "ci_lower_percentile": lo_pct,
                    "ci_upper_percentile": hi_pct,
                    "ci_lower_bca": lo_bca,
                    "ci_upper_bca": hi_bca,
                    "n_iterations": args.n_iterations,
                })

    table = build_supplementary_table_s2(all_rows)
    write_outputs(table, args.csv_out, args.md_out)
    total_elapsed = time.time() - t_start

    print(f"\nWall time: {total_elapsed:.1f}s for {n_cells} cells "
          f"({args.n_iterations} iterations each)", file=sys.stderr)
    print(f"CSV: {args.csv_out}", file=sys.stderr)
    print(f"MD:  {args.md_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
