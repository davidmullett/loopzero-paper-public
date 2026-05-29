#!/usr/bin/env python3
"""
analysis/14b_a1_recsys_horizon_variants.py

A1 quantile detector — recommender robustness horizons (h=40 and h=60).

Companion to analysis/14_build_a1_quantile_detector_v1.py. Computes the A1
sensitivity grid (q ∈ {90, 95, 99} × k ∈ {1, 3, 5}) on the two adjacent-horizon
robustness packets produced by run_horizon_40_pipeline and
run_horizon_60_pipeline, to extend manuscript Table 1 from two rows (markets
canonical + recsys h=50 canonical) to four rows (… + recsys h=40 + recsys h=60).

This script REUSES the canonical detector module verbatim — column resolution,
pre-collapse filtering, reference-row selection, quantile computation, firing
rule, and unit-level aggregation are all called from analysis/14_build_a1_
quantile_detector_v1.py. The only addition is a parameterized loader
(load_packet_per_step_panel) and two custom DomainSpec instances with distinct
benchmark_id values. This guarantees the h=40 and h=60 operating points are
numerically identical to what the canonical detector would produce on the
same panel data.

Reads:
  results/robustness/recommender/movielens25m_recursive_frontier_public_v1__horizon_40_packet/
    results/manifests/movielens25m_recursive_frontier_public_v1__telemetry_panel.csv.gz
  results/robustness/recommender/movielens25m_recursive_frontier_public_v1__horizon_60_packet/
    results/manifests/movielens25m_recursive_frontier_public_v1__telemetry_panel.csv.gz

Writes:
  results/rendered/bridge/a1_loopzero_operating_points_h40_h60.csv
  results/rendered/bridge/a1_loopzero_operating_points_h40_h60.md
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Repository root + canonical-detector import
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Module name starts with a digit → must use importlib.import_module
_a1 = importlib.import_module("analysis.14_build_a1_quantile_detector_v1")

# Reuse module-level constants and helpers
G_CANDIDATES = _a1.G_CANDIDATES
P_CANDIDATES = _a1.P_CANDIDATES
D_CANDIDATES = _a1.D_CANDIDATES
HORIZON_CANDIDATES = _a1.HORIZON_CANDIDATES
PRECOLLAPSE_FLAG_CANDIDATES = _a1.PRECOLLAPSE_FLAG_CANDIDATES
PRECOLLAPSE_ROLE_CANDIDATES = _a1.PRECOLLAPSE_ROLE_CANDIDATES
KIND_CANDIDATES = _a1.KIND_CANDIDATES
UNIT_ID_CANDIDATES = _a1.UNIT_ID_CANDIDATES
STEP_CANDIDATES = _a1.STEP_CANDIDATES
DOMAIN_RECSYS = _a1.DOMAIN_RECSYS

choose_column = _a1.choose_column
choose_column_optional = _a1.choose_column_optional
run_configuration = _a1.run_configuration
enumerate_grid_cells = _a1.enumerate_grid_cells
write_a1_table = _a1.write_a1_table
DomainSpec = _a1.DomainSpec


# ---------------------------------------------------------------------------
# Parameterized loader — mirrors canonical load_recsys_per_step_panel exactly;
# only the panel path and the horizon filter target are parameters.
# ---------------------------------------------------------------------------
def load_packet_per_step_panel(packet_dir: Path, horizon: int) -> pd.DataFrame:
    """Return per-step panel for one horizon-robustness packet, restricted to
    pre-collapse rows. Logic mirrors canonical load_recsys_per_step_panel
    (analysis/14_build_a1_quantile_detector_v1.py:204).

    Output columns: unit_id, kind ∈ {event, control}, step, G, p, delta.
    NaN rows in (G, p, delta) are dropped (pre-reg §4).
    """
    panel_path = (
        packet_dir
        / "results"
        / "manifests"
        / "movielens25m_recursive_frontier_public_v1__telemetry_panel.csv.gz"
    )
    if not panel_path.exists():
        raise FileNotFoundError(
            f"[h{horizon}] telemetry panel not found at {panel_path}"
        )
    df = pd.read_csv(panel_path, compression="gzip")

    g_col = choose_column(df, G_CANDIDATES, f"h{horizon}:G")
    p_col = choose_column(df, P_CANDIDATES, f"h{horizon}:p")
    d_col = choose_column(df, D_CANDIDATES, f"h{horizon}:delta")

    # Horizon filter — same logic as canonical, target parameterized
    horizon_col = choose_column_optional(df, HORIZON_CANDIDATES)
    if horizon_col is not None:
        h = pd.to_numeric(df[horizon_col], errors="coerce")
        mask = h.eq(horizon)
        if mask.any():
            df = df.loc[mask].copy()

    # Pre-collapse filter — identical to canonical
    precollapse_flag_col = choose_column_optional(df, PRECOLLAPSE_FLAG_CANDIDATES)
    if precollapse_flag_col is not None:
        flag = df[precollapse_flag_col]
        if pd.api.types.is_bool_dtype(flag):
            df = df.loc[flag].copy()
        else:
            df = df.loc[
                pd.to_numeric(flag, errors="coerce").fillna(0).astype(int).eq(1)
            ].copy()
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
        raise KeyError(f"[h{horizon}] could not infer event/control kind column")

    unit_col = choose_column_optional(df, UNIT_ID_CANDIDATES)
    if unit_col is None:
        raise KeyError(f"[h{horizon}] could not infer unit id column")

    step_col = choose_column_optional(df, STEP_CANDIDATES)
    if step_col is None:
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

    mixed = (
        out.groupby("unit_id")["kind"].nunique().reset_index().query("kind > 1")
    )
    if not mixed.empty:
        raise RuntimeError(
            f"[h{horizon}] units with mixed event/control kind tagging: "
            f"{mixed['unit_id'].tolist()[:5]}... — pre-reg §1 forbids this."
        )

    return out


# ---------------------------------------------------------------------------
# Custom DomainSpec instances. domain=DOMAIN_RECSYS so select_reference_rows
# applies the canonical recsys reference-selection logic. benchmark_id
# distinguishes h=40 from h=60 in the output rows.
# ---------------------------------------------------------------------------
RECSYS_HORIZON_SPECS: dict[int, "DomainSpec"] = {
    40: DomainSpec(
        domain=DOMAIN_RECSYS,
        benchmark_id="movielens25m_recursive_frontier_public_v1__horizon_40",
        order_col="step",
    ),
    60: DomainSpec(
        domain=DOMAIN_RECSYS,
        benchmark_id="movielens25m_recursive_frontier_public_v1__horizon_60",
        order_col="step",
    ),
}

PACKET_DIRS: dict[int, Path] = {
    40: REPO_ROOT
    / "results"
    / "robustness"
    / "recommender"
    / "movielens25m_recursive_frontier_public_v1__horizon_40_packet",
    60: REPO_ROOT
    / "results"
    / "robustness"
    / "recommender"
    / "movielens25m_recursive_frontier_public_v1__horizon_60_packet",
}


def main() -> int:
    out_dir = REPO_ROOT / "results" / "rendered" / "bridge"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "a1_loopzero_operating_points_h40_h60.csv"
    out_md = out_dir / "a1_loopzero_operating_points_h40_h60.md"

    all_rows: list[dict] = []
    for horizon in (40, 60):
        spec = RECSYS_HORIZON_SPECS[horizon]
        packet_dir = PACKET_DIRS[horizon]
        print(
            f"[h{horizon}] loading panel from {packet_dir.name}",
            file=sys.stderr,
        )
        panel = load_packet_per_step_panel(packet_dir, horizon)
        n_units = panel["unit_id"].nunique()
        n_event = (panel["kind"] == "event").sum()
        n_ctrl = (panel["kind"] == "control").sum()
        print(
            f"[h{horizon}] panel: {len(panel)} rows; "
            f"{n_units} units; {n_event} event rows; {n_ctrl} control rows",
            file=sys.stderr,
        )

        for q_G_pct, q_p_pct, q_delta_pct, k in enumerate_grid_cells():
            row = run_configuration(spec, panel, q_G_pct, q_p_pct, q_delta_pct, k)
            all_rows.append(row)

    table = pd.DataFrame(all_rows)
    write_a1_table(table, out_csv, out_md)

    print()
    print(f"CSV: {out_csv}")
    print(f"MD:  {out_md}")
    print()
    print(table.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
