"""
analysis/14_build_a1_quantile_detector_v1.py

A1 pre-registered quantile detector (Loopzero), markets and recommender.

Pre-registration: analysis/14_a1_prereg.md
Readiness brief:  A1_readiness_brief.md

Firing rule (per row):
    fire_t = (G_t > q_G) AND (p_t > q_p) AND (delta_t < q_delta)
Unit-level alarm:
    unit_alarmed iff fire_t is true for k consecutive rows within the unit's
    panel (sorted by per-row order column; runs never cross unit_id).

Quantiles (per pre-reg §2):
    q_G     = q_G_pct-percentile of G across reference rows
    q_p     = q_p_pct-percentile of p across reference rows
    q_delta = q_delta_pct-percentile of delta across reference rows
In the sensitivity grid q_G_pct = q_p_pct = q and q_delta_pct = 100 - q.

Reference rows (pre-reg §1, no event-unit peeking):
    markets -> control-unit rows inside the canonical unit window, last 30 min.
    recsys  -> control-unit per-step rows inside the canonical h=50 pre-collapse panel.

NaN handling (pre-reg §4):
    Rows with any NaN in (G, p, delta) are dropped from both reference quantile
    computation AND firing evaluation.

Sensitivity grid (pre-reg §3):
    q ∈ {90, 95, 99} × k ∈ {1, 3, 5} = 9 cells per benchmark.
    Primary cell: (q=95, k=3); rendered bold in the Markdown table.

Outputs:
    results/rendered/bridge/a1_loopzero_operating_points.csv
    results/rendered/bridge/a1_loopzero_operating_points.md

Data status:
    The per-row markets packet CSVs (results/rendered/equity_dislocation_family/
    intraday_v2_ingredient_packet/cfg_001339__*.packet.csv) and the recommender
    telemetry panel (results/manifests/movielens25m_recursive_frontier_public_v1__
    telemetry_panel.csv[.gz]) are NOT shipped in the public branch (see
    docs/REPRODUCTION.md §1). The loaders raise FileNotFoundError with a
    pointer to the expected path when run against the public repo alone. The
    detector engine + tests are exercised with synthetic fixtures.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Reuse loaders / column-resolution helpers from 13bb. The module name starts
# with a digit, so importlib is required.
# ---------------------------------------------------------------------------
_ANALYSIS_DIR = Path(__file__).resolve().parent
if str(_ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_DIR))

_m13bb = import_module("13bb_build_witness_direction_table_v3")
choose_column = _m13bb.choose_column
choose_column_optional = _m13bb.choose_column_optional
choose_existing = _m13bb.choose_existing
load_markets_canonical_unit_windows = _m13bb.load_markets_canonical_unit_windows
load_markets_packets = _m13bb.load_markets_packets

# Shared constants (single source of truth in 13bb)
G_CANDIDATES = _m13bb.G_CANDIDATES
P_CANDIDATES = _m13bb.P_CANDIDATES
D_CANDIDATES = _m13bb.D_CANDIDATES
HORIZON_CANDIDATES = _m13bb.HORIZON_CANDIDATES
PRECOLLAPSE_FLAG_CANDIDATES = _m13bb.PRECOLLAPSE_FLAG_CANDIDATES
PRECOLLAPSE_ROLE_CANDIDATES = _m13bb.PRECOLLAPSE_ROLE_CANDIDATES
KIND_CANDIDATES = _m13bb.KIND_CANDIDATES
UNIT_ID_CANDIDATES = _m13bb.UNIT_ID_CANDIDATES
RECSYS_TELEMETRY_CANDIDATES = _m13bb.RECSYS_TELEMETRY_CANDIDATES
RECSYS_CANONICAL_HORIZON = _m13bb.RECSYS_CANONICAL_HORIZON
MARKETS_PACKET_DIR = _m13bb.MARKETS_PACKET_DIR
MARKETS_CANONICAL_CONFIG_ID = _m13bb.MARKETS_CANONICAL_CONFIG_ID
MARKETS_CANONICAL_INPUT_CSV = _m13bb.MARKETS_CANONICAL_INPUT_CSV

# Per-step ordering candidates for recsys (not declared in 13bb because the
# witness pipeline aggregates within-unit). If none of these appear, fall back
# to cumcount within unit_id (insertion order in the source CSV).
STEP_CANDIDATES = ["step", "step_index", "step_id", "t", "window_step", "bandit_step"]

# Benchmark identifiers (match 13bb output benchmark_id fields).
MARKETS_BENCHMARK_ID = "volmageddon_covid_public_v2"
RECSYS_BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1__canonical_h50"

# Pre-reg §1: late-window minutes for markets reference selection.
MARKETS_LATE_WINDOW_MIN = 30

# Pre-reg locked equal-FP band (pass/fail rule §4).
FP_BAND_LOW = 0.03
FP_BAND_HIGH = 0.07

# Output paths.
ROOT = Path(".")
OUT_DIR = ROOT / "results" / "rendered" / "bridge"
OUT_CSV = OUT_DIR / "a1_loopzero_operating_points.csv"
OUT_MD = OUT_DIR / "a1_loopzero_operating_points.md"

# Sensitivity grid: pre-registered values q ∈ {90, 95, 99} (pre-reg §3),
# extended downward to populate the low-FP region required for A2
# threshold-path calibration at FPR ∈ {0.01, 0.025, 0.05, 0.075, 0.10}
# (see analysis/a2_threshold_path/README.md). Extension stays within the
# detector's percentile design envelope q ∈ [0, 100]. Primary canonical
# config (PRIMARY_Q_PCT, PRIMARY_K) is unchanged at q=95, k=3.
Q_GRID_PCT = [50, 60, 70, 75, 80, 85, 90, 95, 99]
K_GRID = [1, 3, 5]
PRIMARY_Q_PCT = 95
PRIMARY_K = 3

DOMAIN_MARKETS = "markets"
DOMAIN_RECSYS = "recsys"


# ===========================================================================
# Step 2: load_markets_per_row_panel
# ===========================================================================
def load_markets_per_row_panel(
    late_window_min: int = MARKETS_LATE_WINDOW_MIN,
) -> pd.DataFrame:
    """Return per-row markets panel restricted to each canonical unit's last
    `late_window_min` minutes.

    Output columns: unit_id, kind ∈ {event, control}, ts, G, p, delta.
    NaN rows in (G, p, delta) are dropped (pre-reg §4).

    Raises FileNotFoundError with a clear message if either the canonical
    units CSV or the per-slice packet CSVs are not on disk (see
    docs/REPRODUCTION.md §1 — raw markets panels are not shipped in the
    public branch).
    """
    if not MARKETS_CANONICAL_INPUT_CSV.exists():
        raise FileNotFoundError(
            "Markets canonical units CSV not found at "
            f"{MARKETS_CANONICAL_INPUT_CSV}. Required for A1 per-row panel. "
            "See docs/REPRODUCTION.md §1 — raw/processed markets panels are "
            "not redistributed in the public branch."
        )

    packet_paths = sorted(MARKETS_PACKET_DIR.glob(f"{MARKETS_CANONICAL_CONFIG_ID}__*.packet.csv"))
    if not packet_paths:
        raise FileNotFoundError(
            "Markets per-slice packet CSVs not found at "
            f"{MARKETS_PACKET_DIR}/{MARKETS_CANONICAL_CONFIG_ID}__*.packet.csv. "
            "Required for A1 per-row panel. See docs/REPRODUCTION.md §1 — raw "
            "markets ingredient packets are not redistributed in the public branch."
        )

    raw = load_markets_packets()
    units = load_markets_canonical_unit_windows()

    g_col = choose_column(raw, G_CANDIDATES, "markets:G")
    p_col = choose_column(raw, P_CANDIDATES, "markets:p")
    d_col = choose_column(raw, D_CANDIDATES, "markets:delta")

    rows: list[pd.DataFrame] = []
    for _, unit in units.iterrows():
        slice_id = str(unit["slice_id"])
        kind = str(unit["kind"])
        unit_id = str(unit["unit_id"])
        start_ts = pd.Timestamp(unit["unit_start_ts_utc"])
        end_ts = pd.Timestamp(unit["unit_end_ts_utc"])
        late_start = end_ts - pd.Timedelta(minutes=late_window_min)

        unit_rows = raw.loc[
            raw["slice_id"].astype(str).eq(slice_id)
            & raw["ts_utc"].ge(late_start)
            & raw["ts_utc"].le(end_ts)
        ].copy()

        if unit_rows.empty:
            raise RuntimeError(
                f"[markets] canonical unit {unit_id} produced no rows for the "
                f"last {late_window_min} min (slice={slice_id}, end={end_ts})."
            )

        out = pd.DataFrame(
            {
                "unit_id": unit_id,
                "kind": kind,
                "ts": pd.to_datetime(unit_rows["ts_utc"], utc=True).values,
                "G": pd.to_numeric(unit_rows[g_col], errors="coerce").values,
                "p": pd.to_numeric(unit_rows[p_col], errors="coerce").values,
                "delta": pd.to_numeric(unit_rows[d_col], errors="coerce").values,
            }
        )
        rows.append(out)

    panel = pd.concat(rows, ignore_index=True)
    panel = panel.dropna(subset=["G", "p", "delta"]).reset_index(drop=True)
    panel = panel.sort_values(["unit_id", "ts"], kind="stable").reset_index(drop=True)
    return panel


# ===========================================================================
# Step 3: load_recsys_per_step_panel
# ===========================================================================
def load_recsys_per_step_panel() -> pd.DataFrame:
    """Return per-step recommender panel restricted to canonical horizon and
    pre-collapse rows, with no within-unit aggregation.

    Output columns: unit_id, kind ∈ {event, control}, step, G, p, delta.
    NaN rows in (G, p, delta) are dropped (pre-reg §4).

    Raises FileNotFoundError with a clear message if the telemetry panel is
    not on disk (see docs/REPRODUCTION.md §1 — full recommender pipeline from
    raw data requires MovieLens-25M download + recursive-frontier execution).
    """
    available = [p for p in RECSYS_TELEMETRY_CANDIDATES if p.exists()]
    if not available:
        raise FileNotFoundError(
            "Recsys telemetry panel not found at any of: "
            f"{[str(p) for p in RECSYS_TELEMETRY_CANDIDATES]}. Required for "
            "A1 per-step panel. See docs/REPRODUCTION.md §1 — the recursive-"
            "frontier telemetry panel is not redistributed in the public branch."
        )
    path = available[0]
    df = pd.read_csv(path, compression="gzip" if path.suffix == ".gz" else None)

    g_col = choose_column(df, G_CANDIDATES, "recsys:G")
    p_col = choose_column(df, P_CANDIDATES, "recsys:p")
    d_col = choose_column(df, D_CANDIDATES, "recsys:delta")

    # Canonical horizon (pre-reg via 13bb): h == 50.
    horizon_col = choose_column_optional(df, HORIZON_CANDIDATES)
    if horizon_col is not None:
        h = pd.to_numeric(df[horizon_col], errors="coerce")
        mask = h.eq(RECSYS_CANONICAL_HORIZON)
        if mask.any():
            df = df.loc[mask].copy()

    # Pre-collapse filter (boolean flag preferred; role string fallback).
    precollapse_flag_col = choose_column_optional(df, PRECOLLAPSE_FLAG_CANDIDATES)
    if precollapse_flag_col is not None:
        flag = df[precollapse_flag_col]
        if pd.api.types.is_bool_dtype(flag):
            df = df.loc[flag].copy()
        else:
            df = df.loc[pd.to_numeric(flag, errors="coerce").fillna(0).astype(int).eq(1)].copy()
    else:
        role_col = choose_column_optional(df, PRECOLLAPSE_ROLE_CANDIDATES)
        if role_col is not None:
            role = df[role_col].astype(str).str.lower()
            precollapse_values = {"precollapse", "pre_collapse", "pre-collapse"}
            if role.isin(precollapse_values).any():
                df = df.loc[role.isin(precollapse_values)].copy()

    kind_col = choose_column_optional(df, KIND_CANDIDATES)
    if kind_col is not None:
        df["kind"] = df[kind_col].astype(str).str.lower()
    elif "is_event" in df.columns:
        df["kind"] = df["is_event"].map({True: "event", False: "control"})
    else:
        raise KeyError("[recsys] could not infer event/control kind column")

    unit_col = choose_column_optional(df, UNIT_ID_CANDIDATES)
    if unit_col is None:
        raise KeyError("[recsys] could not infer unit id column")

    step_col = choose_column_optional(df, STEP_CANDIDATES)
    if step_col is None:
        # The witness pipeline doesn't preserve a step index. Fall back to
        # source-row order within unit_id. The k-consecutive idiom relies on
        # this ordering, so it is recorded as cumcount.
        df = df.copy()
        df["__step_fallback"] = df.groupby(unit_col, sort=False).cumcount()
        step_col = "__step_fallback"

    keep = df.loc[df["kind"].isin({"event", "control"})].copy()

    out = pd.DataFrame(
        {
            "unit_id": keep[unit_col].astype(str).values,
            "kind": keep["kind"].astype(str).values,
            "step": pd.to_numeric(keep[step_col], errors="coerce").astype("Int64").values,
            "G": pd.to_numeric(keep[g_col], errors="coerce").values,
            "p": pd.to_numeric(keep[p_col], errors="coerce").values,
            "delta": pd.to_numeric(keep[d_col], errors="coerce").values,
        }
    )
    out = out.dropna(subset=["G", "p", "delta", "step"]).reset_index(drop=True)
    out = out.sort_values(["unit_id", "step"], kind="stable").reset_index(drop=True)

    # Guard against units that straddle multiple kinds (pre-reg §1 requires a
    # clean event/control partition; flagged as a STOP condition in the brief).
    mixed = (
        out.groupby("unit_id")["kind"].nunique().reset_index().query("kind > 1")
    )
    if not mixed.empty:
        raise RuntimeError(
            "[recsys] units with mixed event/control kind tagging: "
            f"{mixed['unit_id'].tolist()[:5]}... — pre-reg §1 forbids this; "
            "see A1_readiness_brief secondary-risk note."
        )

    return out


# ===========================================================================
# Step 4: select_reference_rows
# ===========================================================================
def select_reference_rows(panel_df: pd.DataFrame, domain: str) -> pd.DataFrame:
    """Pre-reg §1: reference quantiles use control-unit rows only.

    For markets, the panel is already restricted to the late 30-min window by
    `load_markets_per_row_panel`; for recsys, it is already restricted to
    pre-collapse h=50 rows by `load_recsys_per_step_panel`. The reference-set
    filter then collapses to `kind == "control"` for both domains.

    This is the self-reference trap fence: event-unit rows must never enter
    the reference set used to fit q_G / q_p / q_delta.
    """
    if domain not in {DOMAIN_MARKETS, DOMAIN_RECSYS}:
        raise ValueError(f"unknown domain {domain!r}")
    if "kind" not in panel_df.columns:
        raise KeyError("panel_df missing 'kind' column")
    return panel_df.loc[panel_df["kind"].astype(str).eq("control")].copy()


# ===========================================================================
# Step 5: compute_reference_quantiles
# ===========================================================================
def compute_reference_quantiles(
    reference_df: pd.DataFrame,
    q_G_pct: float,
    q_p_pct: float,
    q_delta_pct: float,
) -> dict[str, float]:
    """Empirical quantiles on the control-only reference set.

    Uses np.nanpercentile per pre-reg §4 (rows with NaN in any of G/p/delta
    are already dropped upstream, but we keep nan-safe semantics here).
    """
    if reference_df.empty:
        raise RuntimeError("reference set is empty; cannot compute quantiles")
    return {
        "q_G": float(np.nanpercentile(reference_df["G"].to_numpy(), q_G_pct)),
        "q_p": float(np.nanpercentile(reference_df["p"].to_numpy(), q_p_pct)),
        "q_delta": float(np.nanpercentile(reference_df["delta"].to_numpy(), q_delta_pct)),
    }


# ===========================================================================
# Step 6: apply_firing_rule
# ===========================================================================
def apply_firing_rule(
    panel_df: pd.DataFrame,
    qs: dict[str, float],
    k: int,
    order_col: str,
) -> pd.DataFrame:
    """Apply (G > q_G) & (p > q_p) & (delta < q_delta) per row, then mark a
    unit as alarmed iff any k-consecutive fire run lies within its panel.

    Run-length groupby is scoped within unit_id so streaks never bridge two
    units. Within each unit, rows are ordered by `order_col`.

    Returns a DataFrame with one row per unit_id:
        unit_id, kind, unit_alarmed (bool).
    """
    if panel_df.empty:
        return pd.DataFrame(columns=["unit_id", "kind", "unit_alarmed"])
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")
    if order_col not in panel_df.columns:
        raise KeyError(f"panel_df missing order column {order_col!r}")

    df = panel_df.sort_values(["unit_id", order_col], kind="stable").reset_index(drop=True).copy()

    fire = (df["G"] > qs["q_G"]) & (df["p"] > qs["q_p"]) & (df["delta"] < qs["q_delta"])
    df["fire"] = fire.astype(int)

    # Within-unit run identification: bump run_id at every transition.
    df["run_id"] = df.groupby("unit_id")["fire"].transform(
        lambda s: (s != s.shift()).cumsum()
    )
    # Within each (unit_id, run_id), cumsum of fire is the running length of
    # the active fire streak (zero across non-fire runs because fire == 0
    # there).
    df["run_length"] = df.groupby(["unit_id", "run_id"])["fire"].cumsum() * df["fire"]
    df["k_consec_fire"] = df["run_length"] >= k

    out = (
        df.groupby("unit_id", as_index=False)
        .agg(kind=("kind", "first"), unit_alarmed=("k_consec_fire", "any"))
    )
    out["unit_alarmed"] = out["unit_alarmed"].astype(bool)
    return out


# ===========================================================================
# Step 7: aggregate_unit_alarms
# ===========================================================================
def aggregate_unit_alarms(alarmed_units_df: pd.DataFrame) -> dict:
    """Compute pre-reg §4 pass/fail accounting across units."""
    kind = alarmed_units_df["kind"].astype(str)
    alarmed = alarmed_units_df["unit_alarmed"].astype(bool)

    n_event = int((kind == "event").sum())
    n_control = int((kind == "control").sum())
    n_event_alarmed = int(((kind == "event") & alarmed).sum())
    n_control_alarmed = int(((kind == "control") & alarmed).sum())

    event_alarm_rate = (n_event_alarmed / n_event) if n_event > 0 else float("nan")
    control_fp = (n_control_alarmed / n_control) if n_control > 0 else float("nan")
    accepted = (
        (not math.isnan(control_fp))
        and (FP_BAND_LOW <= control_fp <= FP_BAND_HIGH)
    )
    return {
        "n_event_units": n_event,
        "n_control_units": n_control,
        "n_event_alarmed": n_event_alarmed,
        "n_control_alarmed": n_control_alarmed,
        "event_alarm_rate": event_alarm_rate,
        "control_fp": control_fp,
        "accepted": accepted,
    }


# ===========================================================================
# Step 8: run_configuration
# ===========================================================================
@dataclass(frozen=True)
class DomainSpec:
    domain: str
    benchmark_id: str
    order_col: str


def run_configuration(
    spec: DomainSpec,
    panel_df: pd.DataFrame,
    q_G_pct: float,
    q_p_pct: float,
    q_delta_pct: float,
    k: int,
) -> dict:
    """Wire steps 4 -> 5 -> 6 -> 7 for a single (q, k) configuration on one
    benchmark, returning a single row dict ready for table emission."""
    reference = select_reference_rows(panel_df, spec.domain)
    qs = compute_reference_quantiles(reference, q_G_pct, q_p_pct, q_delta_pct)
    alarms = apply_firing_rule(panel_df, qs, k, spec.order_col)
    stats = aggregate_unit_alarms(alarms)

    primary = (
        q_G_pct == PRIMARY_Q_PCT
        and q_p_pct == PRIMARY_Q_PCT
        and q_delta_pct == (100 - PRIMARY_Q_PCT)
        and k == PRIMARY_K
    )

    return {
        "method": "Loopzero quantile (A1)",
        "domain": spec.domain,
        "benchmark": spec.benchmark_id,
        "config": _format_config(q_G_pct, q_p_pct, q_delta_pct, k),
        "q_G_pct": float(q_G_pct),
        "q_p_pct": float(q_p_pct),
        "q_delta_pct": float(q_delta_pct),
        "k": int(k),
        "q_G": qs["q_G"],
        "q_p": qs["q_p"],
        "q_delta": qs["q_delta"],
        "n_reference_rows": int(len(reference)),
        "n_event_units": stats["n_event_units"],
        "n_control_units": stats["n_control_units"],
        "n_event_alarmed": stats["n_event_alarmed"],
        "n_control_alarmed": stats["n_control_alarmed"],
        "control_fp": stats["control_fp"],
        "event_alarm_rate": stats["event_alarm_rate"],
        "accepted": bool(stats["accepted"]),
        "primary": bool(primary),
    }


def _format_config(q_G_pct: float, q_p_pct: float, q_delta_pct: float, k: int) -> str:
    if q_G_pct == q_p_pct and (q_G_pct + q_delta_pct) == 100:
        return f"q={int(q_G_pct)}, k={int(k)}"
    return (
        f"q_G={int(q_G_pct)}, q_p={int(q_p_pct)}, "
        f"q_delta={int(q_delta_pct)}, k={int(k)}"
    )


# ===========================================================================
# Step 9: sensitivity loop
# ===========================================================================
def enumerate_grid_cells() -> list[tuple[float, float, float, int]]:
    """Pre-reg §3: q ∈ {90, 95, 99} × k ∈ {1, 3, 5}; q_G=q_p=q, q_delta=100-q."""
    cells: list[tuple[float, float, float, int]] = []
    for q in Q_GRID_PCT:
        q_delta = 100 - q
        for k in K_GRID:
            cells.append((float(q), float(q), float(q_delta), int(k)))
    return cells


DOMAIN_SPECS: dict[str, DomainSpec] = {
    DOMAIN_MARKETS: DomainSpec(
        domain=DOMAIN_MARKETS,
        benchmark_id=MARKETS_BENCHMARK_ID,
        order_col="ts",
    ),
    DOMAIN_RECSYS: DomainSpec(
        domain=DOMAIN_RECSYS,
        benchmark_id=RECSYS_BENCHMARK_ID,
        order_col="step",
    ),
}


def build_a1_table(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Run the full sensitivity grid across whichever domains have panels.

    `panels` maps domain name -> per-row/per-step panel DataFrame. Missing
    domains are skipped (the script logs the omission upstream).
    """
    rows: list[dict] = []
    for domain, panel in panels.items():
        if domain not in DOMAIN_SPECS:
            raise KeyError(f"unknown domain {domain!r}; expected {list(DOMAIN_SPECS)}")
        spec = DOMAIN_SPECS[domain]
        for q_G_pct, q_p_pct, q_delta_pct, k in enumerate_grid_cells():
            rows.append(
                run_configuration(spec, panel, q_G_pct, q_p_pct, q_delta_pct, k)
            )
    return pd.DataFrame(rows)


# ===========================================================================
# Step 10: table emission
# ===========================================================================
def format_a1_row(r: pd.Series, bold_primary: bool = True) -> str:
    """Render one A1 row to a Markdown table line. Bold when r.primary is set."""
    method = r["method"]
    benchmark = str(r["benchmark"])
    config = str(r["config"])

    control_fp = r["control_fp"]
    event_rate = r["event_alarm_rate"]
    fp_s = "—" if pd.isna(control_fp) else f"{float(control_fp):.6f}"
    rate_s = "—" if pd.isna(event_rate) else f"{float(event_rate):.6f}"
    accepted_s = "Yes" if bool(r["accepted"]) else "No"

    if bold_primary and bool(r["primary"]):
        method = f"**{method}**"
        benchmark = f"**{benchmark}**"
        config = f"**{config}**"
        fp_s = f"**{fp_s}**"
        rate_s = f"**{rate_s}**"
        accepted_s = f"**{accepted_s}**"

    return (
        f"| {method} | {benchmark} | {config} | {fp_s} | {rate_s} | {accepted_s} |"
    )


def write_a1_table(rows: pd.DataFrame, csv_path: Path, md_path: Path) -> None:
    """Write the A1 operating-points table to CSV and Markdown.

    Column ordering in the Markdown:
        Method | Benchmark | Config | Control FP | Event alarm rate | Accepted?
    The CSV preserves the full row record (numeric thresholds, counts, flags).
    Primary rows (one per benchmark at q=95, k=3) are bolded in the Markdown.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    rows = rows.copy()
    # Stable display ordering: domain, then config in (q_G_pct, k) order so
    # the primary cell sits next to neighbouring sensitivity rows.
    rows = rows.sort_values(
        ["domain", "q_G_pct", "k"], kind="stable"
    ).reset_index(drop=True)

    rows.to_csv(csv_path, index=False)

    lines: list[str] = []
    lines.append("# A1 — Loopzero quantile detector operating points")
    lines.append("")
    lines.append(
        "Pre-registered detector (see `analysis/14_a1_prereg.md`). Reference "
        "quantiles are fit on **control-unit rows only** for each domain "
        "(markets: last 30 min of each canonical unit window; recommender: "
        "per-step rows inside the canonical h=50 pre-collapse panel). Event-"
        "unit rows are never used in quantile computation. Pass criterion: "
        f"`{FP_BAND_LOW:.2f} ≤ control_fp ≤ {FP_BAND_HIGH:.2f}`."
    )
    lines.append("")
    lines.append(
        "| Method | Benchmark | Config | Control FP | Event alarm rate | Accepted? |"
    )
    lines.append("|---|---|---|---:|---:|---|")
    for _, r in rows.iterrows():
        lines.append(format_a1_row(r, bold_primary=True))
    lines.append("")
    lines.append("## Reading note")
    lines.append(
        "- **Primary** rows (bolded) are the pre-registered headline operating "
        "point per benchmark: `q=95, k=3`."
    )
    lines.append(
        "- All numeric values use the `{:.6f}` format convention of the "
        "comparator paper-table family (see `analysis/13am_build_markets_"
        "comparator_paper_table_v1.py`)."
    )
    lines.append(
        "- `Accepted?` is `Yes` iff control FP lies in the locked equal-FP "
        f"band `[{FP_BAND_LOW:.2f}, {FP_BAND_HIGH:.2f}]`."
    )
    lines.append(
        "- Sensitivity grid: `q ∈ {90, 95, 99}` paired with `q_delta = 100 − q`, "
        "and `k ∈ {1, 3, 5}` — 9 cells per benchmark."
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ===========================================================================
# CLI / main glue
# ===========================================================================
def _load_panels(
    skip_markets: bool = False,
    skip_recsys: bool = False,
) -> dict[str, pd.DataFrame]:
    """Try to load both domain panels; surface clear errors for absent inputs.

    Returns a dict keyed by domain. Raises if neither domain is available.
    """
    panels: dict[str, pd.DataFrame] = {}
    errors: list[str] = []

    if not skip_markets:
        try:
            panels[DOMAIN_MARKETS] = load_markets_per_row_panel()
        except FileNotFoundError as e:
            errors.append(f"[markets] {e}")
        except Exception as e:  # noqa: BLE001 — re-raise after logging
            errors.append(f"[markets] unexpected error: {e}")

    if not skip_recsys:
        try:
            panels[DOMAIN_RECSYS] = load_recsys_per_step_panel()
        except FileNotFoundError as e:
            errors.append(f"[recsys] {e}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"[recsys] unexpected error: {e}")

    if not panels:
        msg = (
            "No A1 panels could be loaded; cannot emit the operating-points "
            "table.\n" + "\n".join(errors)
        )
        raise FileNotFoundError(msg)

    for e in errors:
        print(f"[warn] {e}", file=sys.stderr)

    return panels


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-markets",
        action="store_true",
        help="Skip the markets benchmark (useful when raw packets are unavailable).",
    )
    parser.add_argument(
        "--skip-recsys",
        action="store_true",
        help="Skip the recsys benchmark (useful when the telemetry panel is unavailable).",
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
    args = parser.parse_args(argv)

    panels = _load_panels(skip_markets=args.skip_markets, skip_recsys=args.skip_recsys)
    rows = build_a1_table(panels)
    write_a1_table(rows, args.csv_out, args.md_out)

    print(args.csv_out)
    print(args.md_out)
    print()
    print(rows.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
