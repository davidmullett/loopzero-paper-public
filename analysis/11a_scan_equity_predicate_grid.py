
from __future__ import annotations

import itertools
import json
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters_public.equity_dislocation import (
    PRIMARY_SYMBOLS,
    LoopzeroThresholds,
    build_market_state_panel,
    compute_G,
    compute_delta,
    compute_loopzero_alarm,
    compute_p,
)

EVENT_FAMILY = os.environ.get("LZ_EVENT_FAMILY", "equity_dislocations_v1")
PANEL_PARQUET = ROOT / "data" / "public" / "equity_events" / "processed" / "equity_panel_1min.parquet"
PANEL_CSV = ROOT / "data" / "public" / "equity_events" / "processed" / "equity_panel_1min.csv"
PRIMARY_MANIFEST_CSV = ROOT / "results" / "manifests" / "equity_events" / f"{EVENT_FAMILY}.primary_event_manifest.csv"
CONTROL_MANIFEST_CSV = ROOT / "results" / "manifests" / "equity_events" / f"{EVENT_FAMILY}.control_manifest.csv"
MANIFEST_DIR = ROOT / "results" / "manifests" / "equity_events"
SCAN_CSV = MANIFEST_DIR / f"{EVENT_FAMILY}.predicate_grid_scan.csv"
SCAN_ACCEPTED_CSV = MANIFEST_DIR / f"{EVENT_FAMILY}.predicate_grid_scan.accepted.csv"
SCAN_TOP_CSV = MANIFEST_DIR / f"{EVENT_FAMILY}.predicate_grid_scan.top.csv"
SCAN_SUMMARY_JSON = MANIFEST_DIR / f"{EVENT_FAMILY}.predicate_grid_scan.summary.json"
ET_TZ = "America/New_York"

PANEL_REQUIRED_COLUMNS = [
    "ts_utc",
    "ts_et",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "provider",
    "adjustment",
    "event_family",
]

PRIMARY_REQUIRED_COLUMNS = [
    "event_id",
    "event_date",
    "start_ts_utc",
    "collapse_ts_utc",
    "window_end_ts_utc",
    "coverage_status_primary",
]

CONTROL_REQUIRED_COLUMNS = [
    "control_id",
    "matched_to_event_id",
    "event_date",
    "start_ts_utc",
    "end_ts_utc",
    "coverage_status",
]

# Spec v1 search grid
DELTA_WINDOWS = [16, 30, 45, 60]
P_WINDOWS = [16, 30, 45, 60]
G_WINDOWS = [16, 30, 45, 60]
EPS_G_VALUES = [0.01, 0.02, 0.05, 0.10]
TAU_DELTA_VALUES = [-0.05, -0.02, 0.0, 0.02]
TAU_P_VALUES = [0.0, 0.02, 0.05]
P_MIN_VALUES = [0.02, 0.05, 0.10, 0.15, 0.20]
P_Z_THRESHOLDS = [1.0, 1.5, 2.0]

# Softer benchmark-stage gating ladder
K_CONSEC_ALARM_VALUES = [1, 2, 3, 5]
WARMUP_BARS_VALUES = [0, 5, 10, 15]

# Focused p_min scan mode for rapid iteration during adapter design.
# Run with:
#   LZ_FOCUSED_PMIN=1 python analysis/11a_scan_equity_predicate_grid.py
FOCUSED_PMIN_SCAN = os.getenv("LZ_FOCUSED_PMIN", "0") == "1"

TARGET_FP = 0.05
FP_MIN = 0.03
FP_MAX = 0.07
TOP_N = 25


def get_scan_grid() -> dict[str, list[float] | list[int]]:
    if FOCUSED_PMIN_SCAN:
        return {
            "delta_windows": [16, 30, 45],
            "p_windows": [30, 45, 60],
            "g_windows": [8, 16, 30, 45, 60],
            "eps_g_values": [0.02, 0.05, 0.10, 0.15],
            "tau_delta_values": [-0.05, -0.02],
            "tau_p_values": [0.0],
            "p_min_values": [0.02, 0.05, 0.10],
            "p_z_thresholds": [1.0, 1.5],
            "k_consec_alarm_values": [5],
            "warmup_bars_values": [0],
        }

    return {
        "delta_windows": DELTA_WINDOWS,
        "p_windows": P_WINDOWS,
        "g_windows": G_WINDOWS,
        "eps_g_values": EPS_G_VALUES,
        "tau_delta_values": TAU_DELTA_VALUES,
        "tau_p_values": TAU_P_VALUES,
        "p_min_values": P_MIN_VALUES,
        "p_z_thresholds": P_Z_THRESHOLDS,
        "k_consec_alarm_values": K_CONSEC_ALARM_VALUES,
        "warmup_bars_values": WARMUP_BARS_VALUES,
    }


def validate_columns(df: pd.DataFrame, required: list[str], *, name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def load_panel() -> pd.DataFrame:
    if PANEL_PARQUET.exists():
        panel = pd.read_parquet(PANEL_PARQUET)
    elif PANEL_CSV.exists():
        panel = pd.read_csv(PANEL_CSV)
    else:
        raise FileNotFoundError(
            "No processed equity panel found. Expected one of:\n"
            f"  - {PANEL_PARQUET}\n"
            f"  - {PANEL_CSV}"
        )

    validate_columns(panel, PANEL_REQUIRED_COLUMNS, name="processed panel")
    panel = panel.copy()
    panel["ts_utc"] = pd.to_datetime(panel["ts_utc"], utc=True, errors="raise")
    panel["ts_et"] = panel["ts_utc"].dt.tz_convert(ET_TZ)
    panel["symbol"] = panel["symbol"].astype(str).str.upper().str.strip()
    panel = panel.sort_values(["ts_utc", "symbol", "provider"]).reset_index(drop=True)
    return panel


def load_primary_manifest() -> pd.DataFrame:
    if not PRIMARY_MANIFEST_CSV.exists():
        raise FileNotFoundError(f"Missing primary manifest: {PRIMARY_MANIFEST_CSV}")
    manifest = pd.read_csv(PRIMARY_MANIFEST_CSV)
    validate_columns(manifest, PRIMARY_REQUIRED_COLUMNS, name="primary manifest")
    return manifest


def load_control_manifest() -> pd.DataFrame:
    if not CONTROL_MANIFEST_CSV.exists():
        raise FileNotFoundError(f"Missing control manifest: {CONTROL_MANIFEST_CSV}")
    manifest = pd.read_csv(CONTROL_MANIFEST_CSV)
    validate_columns(manifest, CONTROL_REQUIRED_COLUMNS, name="control manifest")
    return manifest


def compute_lead_time_minutes(first_alarm_ts: pd.Timestamp, collapse_ts: pd.Timestamp) -> float:
    return float((collapse_ts - first_alarm_ts).total_seconds() / 60.0)


def compute_lead_time_bars(adapter: pd.DataFrame, first_alarm_ts: pd.Timestamp, collapse_ts: pd.Timestamp) -> int:
    mask = (adapter.index >= first_alarm_ts) & (adapter.index <= collapse_ts)
    count = int(mask.sum())
    return max(count - 1, 0)


def evaluate_events(adapter: pd.DataFrame, primary_manifest: pd.DataFrame) -> dict[str, Any]:
    lead_minutes: list[float] = []
    lead_bars: list[int] = []
    success_ids: list[str] = []
    fail_ids: list[str] = []
    total_alarm_count = 0
    total_pre_collapse_alarm_count = 0

    for _, row in primary_manifest.iterrows():
        event_id = str(row["event_id"])
        start_ts = pd.to_datetime(row["start_ts_utc"], utc=True, errors="raise")
        collapse_ts = pd.to_datetime(row["collapse_ts_utc"], utc=True, errors="raise")
        end_ts = pd.to_datetime(row["window_end_ts_utc"], utc=True, errors="raise")

        window_df = adapter.loc[(adapter.index >= start_ts) & (adapter.index <= end_ts)]
        alarm_df = window_df.loc[window_df["alarm"] == 1]
        pre_collapse_alarm_df = alarm_df.loc[alarm_df.index <= collapse_ts]

        total_alarm_count += int(alarm_df.shape[0])
        total_pre_collapse_alarm_count += int(pre_collapse_alarm_df.shape[0])

        if pre_collapse_alarm_df.empty:
            fail_ids.append(event_id)
            continue

        first_alarm_ts = pre_collapse_alarm_df.index[0]
        lead_minutes.append(compute_lead_time_minutes(first_alarm_ts, collapse_ts))
        lead_bars.append(compute_lead_time_bars(window_df, first_alarm_ts, collapse_ts))
        success_ids.append(event_id)

    return {
        "n_events": int(len(primary_manifest)),
        "n_event_success": int(len(success_ids)),
        "n_event_fail": int(len(fail_ids)),
        "event_success_rate": float(len(success_ids) / len(primary_manifest)) if len(primary_manifest) > 0 else 0.0,
        "event_success_ids": success_ids,
        "event_fail_ids": fail_ids,
        "median_lead_minutes": None if not lead_minutes else float(pd.Series(lead_minutes).median()),
        "median_lead_bars": None if not lead_bars else float(pd.Series(lead_bars).median()),
        "total_alarm_count_events": int(total_alarm_count),
        "total_pre_collapse_alarm_count": int(total_pre_collapse_alarm_count),
    }


def evaluate_controls(adapter: pd.DataFrame, control_manifest: pd.DataFrame) -> dict[str, Any]:
    any_alarm_ids: list[str] = []
    silent_ids: list[str] = []
    total_alarm_rows = 0
    total_control_rows = 0

    for _, row in control_manifest.iterrows():
        control_id = str(row["control_id"])
        start_ts = pd.to_datetime(row["start_ts_utc"], utc=True, errors="raise")
        end_ts = pd.to_datetime(row["end_ts_utc"], utc=True, errors="raise")

        window_df = adapter.loc[(adapter.index >= start_ts) & (adapter.index < end_ts)]
        alarm_df = window_df.loc[window_df["alarm"] == 1]

        total_alarm_rows += int(alarm_df.shape[0])
        total_control_rows += int(window_df.shape[0])

        if alarm_df.empty:
            silent_ids.append(control_id)
        else:
            any_alarm_ids.append(control_id)

    n_controls = len(control_manifest)
    window_fp_rate = float(len(any_alarm_ids) / n_controls) if n_controls > 0 else 0.0
    row_fp_rate = float(total_alarm_rows / total_control_rows) if total_control_rows > 0 else 0.0

    window_fp_accepted = FP_MIN <= window_fp_rate <= FP_MAX
    row_fp_accepted = FP_MIN <= row_fp_rate <= FP_MAX

    return {
        "n_controls": int(n_controls),
        "n_controls_with_alarm": int(len(any_alarm_ids)),
        "n_controls_without_alarm": int(len(silent_ids)),
        "control_alarm_ids": any_alarm_ids,
        "control_silent_ids": silent_ids,
        "control_window_fp_rate": window_fp_rate,
        "control_row_fp_rate": row_fp_rate,
        "control_window_fp_accepted": bool(window_fp_accepted),
        "control_row_fp_accepted": bool(row_fp_accepted),
        "total_control_alarm_rows": int(total_alarm_rows),
        "total_control_rows": int(total_control_rows),
    }


def provisional_score(result: dict[str, Any]) -> float:
    success = result["n_event_success"]
    controls_with_alarm = result["n_controls_with_alarm"]
    n_controls = max(int(result["n_controls"]), 1)
    target_alarm_windows = TARGET_FP * n_controls
    lead_bars = result["median_lead_bars"] if result["median_lead_bars"] is not None else -1e9
    window_fp = result["control_window_fp_rate"]
    row_fp = result["control_row_fp_rate"]
    window_fp_penalty = abs(window_fp - TARGET_FP)
    row_fp_penalty = abs(row_fp - TARGET_FP)
    accepted_bonus = 1 if result["control_window_fp_accepted"] else 0
    controls_distance_penalty = abs(controls_with_alarm - target_alarm_windows)
    return (
        (accepted_bonus * 1_000_000)
        + (success * 10_000)
        - (controls_distance_penalty * 100_000)
        + lead_bars
        - (window_fp_penalty * 10_000)
        - (row_fp_penalty * 1_000)
    )


def build_market_state(panel: pd.DataFrame) -> pd.DataFrame:
    return build_market_state_panel(panel, symbols=PRIMARY_SYMBOLS)


def apply_alarm_gating(
    alarm: pd.Series,
    *,
    k_consec_alarm: int,
    warmup_bars: int,
) -> pd.Series:
    gated = alarm.fillna(0).astype(int).copy()

    if warmup_bars > 0:
        gated.iloc[:warmup_bars] = 0

    if k_consec_alarm <= 1:
        return gated

    run = gated.rolling(window=k_consec_alarm, min_periods=k_consec_alarm).sum()
    gated = (run >= k_consec_alarm).astype(int)
    gated.iloc[: max(warmup_bars, k_consec_alarm - 1)] = 0
    return gated


def expected_grid_size() -> int:
    grid = get_scan_grid()
    return (
        len(grid["delta_windows"])
        * len(grid["p_windows"])
        * len(grid["g_windows"])
        * len(grid["eps_g_values"])
        * len(grid["tau_delta_values"])
        * len(grid["tau_p_values"])
        * len(grid["p_min_values"])
        * len(grid["p_z_thresholds"])
        * len(grid["k_consec_alarm_values"])
        * len(grid["warmup_bars_values"])
    )


def run_scan(panel: pd.DataFrame, primary_manifest: pd.DataFrame, control_manifest: pd.DataFrame) -> pd.DataFrame:
    market_state = build_market_state(panel)
    grid = get_scan_grid()

    delta_windows = list(grid["delta_windows"])
    p_windows = list(grid["p_windows"])
    g_windows = list(grid["g_windows"])
    eps_g_values = list(grid["eps_g_values"])
    tau_delta_values = list(grid["tau_delta_values"])
    tau_p_values = list(grid["tau_p_values"])
    p_min_values = list(grid["p_min_values"])
    p_z_thresholds = list(grid["p_z_thresholds"])
    k_consec_alarm_values = list(grid["k_consec_alarm_values"])
    warmup_bars_values = list(grid["warmup_bars_values"])

    delta_cache = {window: compute_delta(market_state, window=window) for window in delta_windows}
    p_cache = {
        (window, z_threshold): compute_p(market_state, window=window, z_threshold=z_threshold)
        for window in p_windows
        for z_threshold in p_z_thresholds
    }
    g_cache = {window: compute_G(market_state, window=window) for window in g_windows}

    rows: list[dict[str, Any]] = []
    config_idx = 0

    grid = itertools.product(
        delta_windows,
        p_windows,
        g_windows,
        eps_g_values,
        tau_delta_values,
        tau_p_values,
        p_min_values,
        p_z_thresholds,
        k_consec_alarm_values,
        warmup_bars_values,
    )

    for (
        delta_window,
        p_window,
        g_window,
        eps_g,
        tau_delta,
        tau_p,
        p_min,
        p_z_threshold,
        k_consec_alarm,
        warmup_bars,
    ) in grid:
        config_idx += 1
        thresholds = LoopzeroThresholds(
            eps_g=eps_g,
            tau_delta=tau_delta,
            tau_p=tau_p,
            p_min=p_min,
            delta_window=delta_window,
            p_window=p_window,
            g_window=g_window,
        )
        adapter = compute_loopzero_alarm(
            delta_cache[delta_window],
            p_cache[(p_window, p_z_threshold)],
            g_cache[g_window],
            thresholds=thresholds,
        ).copy()
        adapter["alarm_raw"] = adapter["alarm"].fillna(0).astype(int)
        adapter["alarm"] = apply_alarm_gating(
            adapter["alarm_raw"],
            k_consec_alarm=k_consec_alarm,
            warmup_bars=warmup_bars,
        )

        event_metrics = evaluate_events(adapter, primary_manifest)
        control_metrics = evaluate_controls(adapter, control_manifest)

        row = {
            "config_id": f"cfg_{config_idx:06d}",
            "delta_window": delta_window,
            "p_window": p_window,
            "g_window": g_window,
            "eps_g": eps_g,
            "tau_delta": tau_delta,
            "tau_p": tau_p,
            "p_min": p_min,
            "p_z_threshold": p_z_threshold,
            "k_consec_alarm": k_consec_alarm,
            "warmup_bars": warmup_bars,
            **event_metrics,
            **control_metrics,
        }
        row["provisional_score"] = provisional_score(row)
        rows.append(row)

    out = pd.DataFrame(rows)
    out = out.sort_values(
        ["provisional_score", "n_event_success", "n_controls_with_alarm", "median_lead_bars"],
        ascending=[False, False, True, False],
    )
    out = out.reset_index(drop=True)
    return out


def write_summary(scan_df: pd.DataFrame, control_manifest: pd.DataFrame) -> None:
    n_controls = int(len(control_manifest))
    window_fp_feasible = any(FP_MIN <= (k / n_controls) <= FP_MAX for k in range(n_controls + 1)) if n_controls > 0 else False

    accepted_df = scan_df.loc[scan_df["control_window_fp_accepted"]].copy()
    top_df = scan_df.head(TOP_N).copy()

    summary = {
        "event_family": EVENT_FAMILY,
        "grid_size": int(len(scan_df)),
        "grid_size_expected": expected_grid_size(),
        "target_fp": TARGET_FP,
        "fp_min": FP_MIN,
        "fp_max": FP_MAX,
        "n_controls": n_controls,
        "window_fp_feasible_with_current_controls": bool(window_fp_feasible),
        "note": (
            "With 20 control windows, window-level false-positive calibration is now feasible: "
            "1 alarm window out of 20 gives FP = 0.05 exactly. "
            "Accordingly, this scan treats control_window_fp_accepted as the primary acceptance flag, "
            "retains control_row_fp_rate as a secondary density diagnostic, "
            "and applies k-consecutive plus warmup gating."
        ),
        "gating_ladder": {
            "focused_pmin_scan": FOCUSED_PMIN_SCAN,
            "k_consec_alarm_values": get_scan_grid()["k_consec_alarm_values"],
            "warmup_bars_values": get_scan_grid()["warmup_bars_values"],
            "p_min_values": get_scan_grid()["p_min_values"],
        },
        "n_configs_window_fp_accepted": int(len(accepted_df)),
        "n_configs_row_fp_accepted": int(scan_df["control_row_fp_accepted"].sum()) if not scan_df.empty else 0,
        "top_config_ids": top_df["config_id"].astype(str).tolist(),
        "best_config": None if scan_df.empty else scan_df.iloc[0].to_dict(),
    }

    SCAN_SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    accepted_df.to_csv(SCAN_ACCEPTED_CSV, index=False)
    top_df.to_csv(SCAN_TOP_CSV, index=False)


def main() -> None:
    panel = load_panel()
    primary_manifest = load_primary_manifest()
    control_manifest = load_control_manifest()

    print(f"Loaded processed panel with {len(panel)} rows")
    print(f"Loaded primary manifest with {len(primary_manifest)} rows")
    print(f"Loaded control manifest with {len(control_manifest)} rows")
    print("Precomputing market-state adapter series and scanning predicate grid...")
    scan_grid = get_scan_grid()
    print(
        "Gating ladder: "
        f"k_consec={scan_grid['k_consec_alarm_values']}, warmup_bars={scan_grid['warmup_bars_values']}, "
        f"p_min={scan_grid['p_min_values']}, focused_pmin_scan={FOCUSED_PMIN_SCAN}, "
        f"expected_grid_size={expected_grid_size()}"
    )

    scan_df = run_scan(panel, primary_manifest, control_manifest)

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    scan_df.to_csv(SCAN_CSV, index=False)
    write_summary(scan_df, control_manifest)

    accepted_count = int(scan_df["control_window_fp_accepted"].sum()) if not scan_df.empty else 0
    print(f"Wrote full predicate grid scan to {SCAN_CSV}")
    print(f"Wrote accepted provisional scan rows to {SCAN_ACCEPTED_CSV}")
    print(f"Wrote top {TOP_N} provisional scan rows to {SCAN_TOP_CSV}")
    print(f"Wrote scan summary JSON to {SCAN_SUMMARY_JSON}")
    print(f"Configs scanned: {len(scan_df)}")
    print(f"Configs accepted by control window FP: {accepted_count}")
    if not scan_df.empty:
        best = scan_df.iloc[0]
        print(
            "Best provisional config: "
            f"{best['config_id']} | success={int(best['n_event_success'])}/{int(best['n_events'])} "
            f"| controls_with_alarm={int(best['n_controls_with_alarm'])}/{int(best['n_controls'])} "
            f"| median_lead_bars={best['median_lead_bars']} "
            f"| row_fp={best['control_row_fp_rate']:.4f} "
            f"| window_fp={best['control_window_fp_rate']:.4f} "
            f"| k={int(best['k_consec_alarm'])} warmup={int(best['warmup_bars'])}"
        )
    print("Ready for the next phase: benchmark comparators against accepted control-calibrated regions.")


if __name__ == "__main__":
    main()
