#!/usr/bin/env python3
"""
analysis/18_load_a4_roc_data.py

Load and normalize comparator calibration data from five sources into a single
canonical parquet for A4 ROC plotting.

Sources:
  1. results/frozen/comparators/.../comparator_acceptance_matrix_v1.csv   (markets, 964 configs)
  2. results/robustness/recommender/.../horizon_40_packet/.../fast_calibration_matrix.csv
  3. results/robustness/recommender/.../horizon_40_packet/.../slow_calibration_matrix.csv
  4. Same pair for horizon_60
  5. results/manifests/movielens25m_recursive_frontier_public_v1__merged_comparator_summary.json
       (h=50 canonical -- markers only, no full grid on disk)

Output: results/rendered/a4_roc_lowfp/a4_roc_data.parquet
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "results" / "rendered" / "a4_roc_lowfp"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PARQUET = OUT_DIR / "a4_roc_data.parquet"
OUT_CSV = OUT_DIR / "a4_roc_data.csv"  # also write CSV for quick inspection


FAST_FAMILIES = {"variance_ews", "ac1", "ac1_ews", "cusum", "page_hinkley"}
SLOW_FAMILIES = {"matrix_profile", "permutation_entropy"}


def family_group(family: str) -> str:
    if family in FAST_FAMILIES:
        return "fast"
    if family in SLOW_FAMILIES:
        return "slow"
    return "unknown"


# ============================================================================
# Source 1: Markets full grid (acceptance matrix, 964 configs)
# ============================================================================
def load_markets_acceptance_matrix() -> pd.DataFrame:
    path = REPO_ROOT / "results/frozen/comparators/markets_comparator_merged_state_v2__20260421T174702Z/comparator_acceptance_matrix_v1.csv"
    df = pd.read_csv(path)

    # Filter to rows with valid fp_cal (skip unavailable/unreachable cases)
    df = df[df["fp_cal"].notna()].copy()

    # Compute event alarm rate from counts
    n_evt_alarm = df["n_event_alarm_units"].fillna(0).astype(float)
    n_evt_total = df["n_event_units_cal"].astype(float)
    tpr = np.where(n_evt_total > 0, n_evt_alarm / n_evt_total, np.nan)

    n_ctl_alarm = df["n_control_alarm_units"].fillna(0).astype(float)
    nontrivial = (n_ctl_alarm > 0) | (n_evt_alarm > 0)

    return pd.DataFrame({
        "domain": "markets",
        "benchmark": df["instantiation"].astype(str),
        "horizon": np.nan,
        "family": df["detector_family"].astype(str),
        "family_group": df["detector_family"].map(family_group),
        "config_id": df["config_id"].astype(str),
        "params_json": df["param_json"].astype(str),
        "fp": df["fp_cal"].astype(float),
        "tpr": tpr,
        "source_type": "curve_point",
        "marker_category": None,
        "accepted": df["accepted"].fillna(0).astype(bool),
        "nontrivial": nontrivial,
        "band_distance": df["distance_to_band"].astype(float),
    })


# ============================================================================
# Sources 2-4: Recsys h=40 and h=60 calibration matrices
# ============================================================================
def load_recsys_calibration_csv(path: Path, horizon: int, group: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["available"] == True].copy()  # noqa: E712

    return pd.DataFrame({
        "domain": "recsys",
        "benchmark": "movielens25m_recursive_frontier_public_v1",
        "horizon": horizon,
        "family": df["family"].astype(str),
        "family_group": group,  # fast or slow from filename
        "config_id": df["config_id"].astype(str),
        "params_json": df["params_json"].astype(str),
        "fp": df["control_fp"].astype(float),
        "tpr": df["event_alarm_rate"].astype(float),
        "source_type": "curve_point",
        "marker_category": None,
        "accepted": df["accepted"].astype(bool),
        "nontrivial": df["nontrivial"].astype(bool),
        "band_distance": df["band_distance"].astype(float),
    })


# ============================================================================
# Source 5: Recsys h=50 canonical from merged JSON (markers only)
# ============================================================================
def load_recsys_h50_canonical_markers() -> pd.DataFrame:
    path = REPO_ROOT / "results/manifests/movielens25m_recursive_frontier_public_v1__merged_comparator_summary.json"
    with open(path) as f:
        data = json.load(f)

    rows = []
    for group_name in ("fast", "slow"):
        group_data = data["groups"].get(group_name, {})
        for family_name, family_data in group_data.items():
            for marker_key in ("nearest", "nearest_nontrivial"):
                marker = family_data.get(marker_key)
                if not isinstance(marker, dict):
                    continue
                if not marker.get("available", True):
                    continue
                rows.append({
                    "domain": "recsys",
                    "benchmark": data["benchmark_id"],
                    "horizon": 50,
                    "family": family_name,
                    "family_group": group_name,
                    "config_id": marker.get("config_id", ""),
                    "params_json": marker.get("params_json", ""),
                    "fp": float(marker.get("control_fp", np.nan)),
                    "tpr": float(marker.get("event_alarm_rate", np.nan)),
                    "source_type": "selected_marker",
                    "marker_category": marker_key,
                    "accepted": bool(marker.get("accepted", False)),
                    "nontrivial": bool(marker.get("nontrivial", True)),
                    "band_distance": float(marker.get("band_distance", np.nan)),
                })
    return pd.DataFrame(rows)


# ============================================================================
# Main load + write
# ============================================================================
def main() -> int:
    parts = []

    print("Loading markets full grid ...")
    markets = load_markets_acceptance_matrix()
    print(f"  markets: {len(markets):>5} rows, "
          f"{markets['family'].nunique()} families")
    parts.append(markets)

    for horizon in (40, 60):
        for group in ("fast", "slow"):
            path = (REPO_ROOT
                    / f"results/robustness/recommender/movielens25m_recursive_frontier_public_v1__horizon_{horizon}_packet"
                    / "results/manifests"
                    / f"movielens25m_recursive_frontier_public_v1__{group}_calibration_matrix.csv")
            if not path.exists():
                print(f"  WARNING: missing {path}")
                continue
            print(f"Loading recsys h={horizon} {group} calibration ...")
            df = load_recsys_calibration_csv(path, horizon, group)
            print(f"  recsys h={horizon} {group:5}: {len(df):>5} rows, "
                  f"{df['family'].nunique()} families")
            parts.append(df)

    print("Loading recsys h=50 canonical markers from merged JSON ...")
    h50 = load_recsys_h50_canonical_markers()
    print(f"  recsys h=50 markers: {len(h50):>5} rows, "
          f"{h50['family'].nunique()} families, "
          f"{h50['marker_category'].nunique()} marker categories")
    parts.append(h50)

    combined = pd.concat(parts, ignore_index=True)

    # Output
    combined.to_parquet(OUT_PARQUET, index=False)
    combined.to_csv(OUT_CSV, index=False)

    print()
    print(f"Total rows: {len(combined)}")
    print(f"Output:")
    print(f"  {OUT_PARQUET}")
    print(f"  {OUT_CSV}")
    print()
    print("=== Inventory by (domain, horizon, source_type) ===")
    print(combined.groupby(["domain", "horizon", "source_type"], dropna=False).size())
    print()
    print("=== Family coverage by (domain, horizon) ===")
    print(combined.groupby(["domain", "horizon"], dropna=False)["family"]
          .apply(lambda s: sorted(s.unique())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
