from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters_public.equity_dislocation import (  # noqa: E402
    LoopzeroThresholds,
    build_market_state_panel,
    compute_G,
    compute_delta,
    compute_loopzero_alarm,
    compute_p,
)

SCAN_FAMILY = os.environ.get("LZ_SCAN_FAMILY", "equity_dislocations_intraday_v2_valid")
PANEL_PATH = ROOT / "data/public/equity_events/processed/equity_panel_1min.parquet"
PRIMARY_MANIFEST_CSV = ROOT / "results/manifests/equity_events" / f"{SCAN_FAMILY}.primary_event_manifest.csv"
CONTROL_MANIFEST_CSV = ROOT / "results/manifests/equity_events" / f"{SCAN_FAMILY}.control_manifest.csv"
BACKFILL_CONTROL_FAMILY = "equity_dislocations_intraday_v2"
BACKFILL_CONTROL_MANIFEST_CSV = (
    ROOT / "results/manifests/equity_events" / f"{BACKFILL_CONTROL_FAMILY}.control_manifest.csv"
)
RESIDUAL_BACKFILL_CONTROL_IDS = {
    "volmageddon_control_2018_01_25",
    "volmageddon_control_2018_01_29",
    "volmageddon_control_2018_02_08",
}
SCAN_CSV = ROOT / "results/manifests/equity_events" / f"{SCAN_FAMILY}.predicate_grid_scan.csv"

OUT_DIR = ROOT / "results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet"
OUT_SUMMARY_CSV = OUT_DIR / "slice_summary.csv"
OUT_README_MD = OUT_DIR / "README.md"

CORE = ["SPY", "QQQ", "IWM"]
VOL = ["VXX", "UVXY", "SVXY"]
ALL_SYMBOLS = CORE + VOL

EPS = 1e-12
BREADTH_EVENT_MIN_SHARE = 0.5
MIN_RUN_LENGTH = 3

FOCUS_CONFIGS: list[dict[str, Any]] = [
    {
        "config_id": "cfg_001339",
        "label": "primary_near_miss_cfg_001339",
        "target_slices": [
            "volmageddon_2018_xiv",
            "covid_mwcb_2020_03_18",
            "covid_noncollapse_2020_03_11",
            "covid_noncollapse_2020_03_13",
            "volmageddon_control_2018_01_25",
            "volmageddon_control_2018_01_29",
            "volmageddon_control_2018_02_08",
        ],
    },
    {
        "config_id": "cfg_002053",
        "label": "corroborating_cfg_002053",
        "target_slices": [
            "volmageddon_2018_xiv",
            "covid_mwcb_2020_03_18",
            "volmageddon_control_2018_01_25",
            "volmageddon_control_2018_01_29",
            "volmageddon_control_2018_02_08",
            "covid_noncollapse_2020_04_03",
        ],
    },
]


def iso_or_none(ts: pd.Timestamp | None) -> str | None:
    if ts is None or pd.isna(ts):
        return None
    return pd.Timestamp(ts).tz_convert("UTC").isoformat().replace("+00:00", "Z")


def pick_column(df: pd.DataFrame, candidates: list[str], *, name: str) -> str:
    for cand in candidates:
        if cand in df.columns:
            return cand
    raise KeyError(f"Could not find {name} in columns: {sorted(df.columns)}")


def apply_alarm_gating(alarm_raw: pd.Series, *, k_consec: int, warmup_bars: int) -> pd.Series:
    raw = alarm_raw.fillna(0).astype(int)
    gated = raw.rolling(window=k_consec, min_periods=k_consec).sum().eq(k_consec).astype(int)
    if warmup_bars > 0:
        gated.iloc[:warmup_bars] = 0
    gated.name = "alarm_gated"
    return gated


def sustained_run_membership(event: pd.Series, *, min_run_length: int) -> pd.Series:
    values = event.fillna(0).astype(int).to_numpy()
    out = np.zeros(len(values), dtype=int)

    run_start = None
    for i, v in enumerate(values):
        if v == 1 and run_start is None:
            run_start = i
        if v == 0 and run_start is not None:
            run_len = i - run_start
            if run_len >= min_run_length:
                out[run_start:i] = 1
            run_start = None

    if run_start is not None:
        run_len = len(values) - run_start
        if run_len >= min_run_length:
            out[run_start:] = 1

    return pd.Series(out, index=event.index, name="sustained_event")


def longest_run(values: pd.Series) -> int:
    best = 0
    cur = 0
    for v in values.fillna(0).astype(int).tolist():
        if v == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return int(best)


def first_true_ts(values: pd.Series) -> pd.Timestamp | None:
    vals = values.fillna(0).astype(int)
    if vals.eq(1).any():
        return pd.Timestamp(vals[vals.eq(1)].index[0])
    return None


def safe_rate(values: pd.Series) -> float | None:
    if values is None or len(values) == 0:
        return None
    return float(values.astype(float).mean())


def load_primary_manifest() -> pd.DataFrame:
    df = pd.read_csv(PRIMARY_MANIFEST_CSV)
    start_col = pick_column(df, ["start_ts_utc"], name="event start")
    end_col = pick_column(df, ["window_end_ts_utc", "end_ts_utc"], name="event end")
    collapse_col = pick_column(df, ["collapse_ts_utc"], name="collapse time")

    out = df.copy()
    out["start_ts_utc"] = pd.to_datetime(out[start_col], utc=True, errors="raise")
    out["end_ts_utc"] = pd.to_datetime(out[end_col], utc=True, errors="raise")
    out["collapse_ts_utc"] = pd.to_datetime(out[collapse_col], utc=True, errors="raise")
    return out


def _normalize_control_manifest(df: pd.DataFrame) -> pd.DataFrame:
    start_col = pick_column(df, ["start_ts_utc"], name="control start")
    end_col = pick_column(df, ["end_ts_utc", "window_end_ts_utc"], name="control end")

    out = df.copy()
    out["start_ts_utc"] = pd.to_datetime(out[start_col], utc=True, errors="raise")
    out["end_ts_utc"] = pd.to_datetime(out[end_col], utc=True, errors="raise")
    return out


def load_control_manifest() -> pd.DataFrame:
    return _normalize_control_manifest(pd.read_csv(CONTROL_MANIFEST_CSV))


def load_backfill_control_manifest() -> pd.DataFrame:
    if not BACKFILL_CONTROL_MANIFEST_CSV.exists():
        return pd.DataFrame()
    return _normalize_control_manifest(pd.read_csv(BACKFILL_CONTROL_MANIFEST_CSV))


def load_scan() -> pd.DataFrame:
    return pd.read_csv(SCAN_CSV)


def select_event_row(primary: pd.DataFrame, event_id: str) -> pd.Series:
    hit = primary.loc[primary["event_id"] == event_id]
    if hit.empty:
        raise ValueError(f"Missing event_id={event_id}")
    return hit.iloc[0]


def select_control_row(control: pd.DataFrame, control_id: str) -> pd.Series:
    hit = control.loc[control["control_id"] == control_id]
    if hit.empty:
        raise ValueError(f"Missing control_id={control_id}")
    return hit.iloc[0]


def select_scan_row(scan: pd.DataFrame, config_id: str) -> pd.Series:
    hit = scan.loc[scan["config_id"] == config_id]
    if hit.empty:
        raise ValueError(f"Missing config_id={config_id}")
    return hit.iloc[0]


# Robust lookup helpers for missing slices
def maybe_select_event_row(primary: pd.DataFrame, event_id: str) -> pd.Series | None:
    hit = primary.loc[primary["event_id"] == event_id]
    if hit.empty:
        return None
    return hit.iloc[0]



def maybe_select_control_row(control: pd.DataFrame, control_id: str) -> pd.Series | None:
    hit = control.loc[control["control_id"] == control_id]
    if hit.empty:
        return None
    return hit.iloc[0]


def maybe_select_control_row_with_backfill(
    control: pd.DataFrame,
    backfill_control: pd.DataFrame,
    control_id: str,
) -> tuple[pd.Series | None, str | None]:
    row = maybe_select_control_row(control, control_id)
    if row is not None:
        return row, "current"

    if control_id in RESIDUAL_BACKFILL_CONTROL_IDS and not backfill_control.empty:
        backfill_row = maybe_select_control_row(backfill_control, control_id)
        if backfill_row is not None:
            return backfill_row, "backfill"

    return None, None


def threshold_dict(scan_row: pd.Series) -> dict[str, Any]:
    return {
        "delta_window": int(scan_row["delta_window"]),
        "p_window": int(scan_row["p_window"]),
        "g_window": int(scan_row["g_window"]),
        "eps_g": float(scan_row["eps_g"]),
        "tau_delta": float(scan_row["tau_delta"]),
        "tau_p": float(scan_row.get("tau_p", 0.0)),
        "p_min": float(scan_row.get("p_min", 0.0)),
    }


def symbol_return_col(market_state: pd.DataFrame, symbol: str) -> str:
    exact = [c for c in market_state.columns if c == f"{symbol}_log_return"]
    if exact:
        return exact[0]
    pref = [c for c in market_state.columns if c.startswith(f"{symbol}_")]
    if len(pref) == 1:
        return pref[0]
    if not pref:
        raise KeyError(f"Missing return column for {symbol}")
    raise ValueError(f"Ambiguous return columns for {symbol}: {pref}")


def build_adapter(market_state: pd.DataFrame, scan_row: pd.Series) -> tuple[pd.DataFrame, LoopzeroThresholds]:
    thr = LoopzeroThresholds(**threshold_dict(scan_row))

    delta = compute_delta(market_state, window=thr.delta_window)
    p = compute_p(market_state, window=thr.p_window, z_threshold=float(scan_row["p_z_threshold"]))
    G = compute_G(market_state, window=thr.g_window)

    adapter = compute_loopzero_alarm(delta, p, G, thresholds=thr).copy()
    adapter.index = pd.to_datetime(adapter.index, utc=True, errors="raise")
    adapter["alarm_raw"] = adapter["alarm"].astype(int)
    adapter["alarm_gated"] = apply_alarm_gating(
        adapter["alarm_raw"],
        k_consec=int(scan_row["k_consec_alarm"]),
        warmup_bars=int(scan_row["warmup_bars"]),
    )
    return adapter, thr


def build_ingredient_frame(market_state: pd.DataFrame, scan_row: pd.Series, adapter: pd.DataFrame) -> pd.DataFrame:
    p_window = int(scan_row["p_window"])
    g_window = int(scan_row["g_window"])
    z_threshold = float(scan_row["p_z_threshold"])
    p_min = float(scan_row.get("p_min", 0.0))
    eps_g = float(scan_row["eps_g"])

    ret = pd.DataFrame(index=market_state.index)
    for sym in ALL_SYMBOLS:
        ret[sym] = market_state[symbol_return_col(market_state, sym)].astype(float)

    abs_ret = ret.abs()
    roll_mean = abs_ret.rolling(window=p_window, min_periods=p_window).mean()
    roll_std = abs_ret.rolling(window=p_window, min_periods=p_window).std(ddof=0).replace(0.0, np.nan)
    zscore = (abs_ret - roll_mean) / (roll_std + EPS)
    stress_flag = (zscore >= z_threshold).astype(int)

    breadth_count = stress_flag[ALL_SYMBOLS].sum(axis=1)
    breadth_share = breadth_count / float(len(ALL_SYMBOLS))

    core_downside_flag = (ret[CORE] < 0).astype(int)
    core_downside_count = core_downside_flag.sum(axis=1)
    core_downside_share = core_downside_count / float(len(CORE))

    vol_complex_count = stress_flag[VOL].sum(axis=1)
    vol_complex_share = vol_complex_count / float(len(VOL))

    breadth_event = (breadth_share >= BREADTH_EVENT_MIN_SHARE).astype(int)
    sustained_event = sustained_run_membership(breadth_event, min_run_length=MIN_RUN_LENGTH)

    raw_p_debug = sustained_event.rolling(window=p_window, min_periods=p_window).mean()
    raw_p_debug = raw_p_debug.ffill().fillna(0.0)
    cond_p_debug = (raw_p_debug >= p_min).astype(int)

    core_stress = abs_ret[CORE].mean(axis=1)
    vol_stress = abs_ret[VOL].mean(axis=1)
    dominance_raw = vol_stress / (core_stress + EPS)
    dominance_baseline = dominance_raw.shift(1).rolling(window=g_window, min_periods=g_window).median()
    G_debug = dominance_raw / (dominance_baseline + EPS)
    G_debug = G_debug.ffill().fillna(0.0)
    cond_gain_debug = (G_debug >= (1.0 + eps_g)).astype(int)

    out = pd.DataFrame(index=market_state.index)

    for sym in ALL_SYMBOLS:
        out[f"{sym}_return"] = ret[sym]
        out[f"{sym}_abs_return"] = abs_ret[sym]
        out[f"{sym}_stress_flag"] = stress_flag[sym]

    out["breadth_count"] = breadth_count
    out["breadth_share"] = breadth_share
    out["core_downside_count"] = core_downside_count
    out["core_downside_share"] = core_downside_share
    out["vol_complex_count"] = vol_complex_count
    out["vol_complex_share"] = vol_complex_share
    out["breadth_event"] = breadth_event
    out["sustained_event"] = sustained_event
    out["raw_p_debug"] = raw_p_debug
    out["cond_p_debug"] = cond_p_debug

    out["G_numerator_vol_stress"] = vol_stress
    out["G_denominator_core_stress"] = core_stress
    out["dominance_raw"] = dominance_raw
    out["dominance_baseline"] = dominance_baseline
    out["G_debug"] = G_debug
    out["cond_gain_debug"] = cond_gain_debug

    keep_adapter_cols = [
        "delta",
        "p",
        "G",
        "delta_change",
        "p_change",
        "cond_gain",
        "cond_delta",
        "cond_p",
        "alarm_raw",
        "alarm_gated",
    ]
    out = out.join(adapter[keep_adapter_cols], how="left")
    out["p_diff_abs"] = (out["raw_p_debug"] - out["p"]).abs()
    out["G_diff_abs"] = (out["G_debug"] - out["G"]).abs()
    return out


def write_packet(df: pd.DataFrame, *, config_id: str, slice_id: str) -> Path:
    out = OUT_DIR / f"{config_id}__{slice_id}.packet.csv"
    df.to_csv(out, index=False)
    return out


def summarize_block(
    *,
    block: pd.DataFrame,
    config_id: str,
    config_label: str,
    slice_id: str,
    kind: str,
    collapse_ts_utc: pd.Timestamp | None,
    packet_path: Path,
) -> dict[str, Any]:
    if collapse_ts_utc is not None:
        pre = block.loc[block["ts_utc"] < collapse_ts_utc].copy()
    else:
        pre = block.copy()

    first_cond_p_ts = first_true_ts(pre.set_index("ts_utc")["cond_p"]) if not pre.empty else None
    first_alarm_raw_ts = first_true_ts(pre.set_index("ts_utc")["alarm_raw"]) if not pre.empty else None
    first_alarm_gated_ts = first_true_ts(pre.set_index("ts_utc")["alarm_gated"]) if not pre.empty else None

    lead_minutes_cond_p = None
    lead_minutes_alarm_raw = None
    lead_minutes_alarm_gated = None

    if collapse_ts_utc is not None and first_cond_p_ts is not None:
        lead_minutes_cond_p = float((collapse_ts_utc - first_cond_p_ts).total_seconds() / 60.0)
    if collapse_ts_utc is not None and first_alarm_raw_ts is not None:
        lead_minutes_alarm_raw = float((collapse_ts_utc - first_alarm_raw_ts).total_seconds() / 60.0)
    if collapse_ts_utc is not None and first_alarm_gated_ts is not None:
        lead_minutes_alarm_gated = float((collapse_ts_utc - first_alarm_gated_ts).total_seconds() / 60.0)

    return {
        "config_label": config_label,
        "config_id": config_id,
        "slice_id": slice_id,
        "kind": kind,
        "collapse_ts_utc": iso_or_none(collapse_ts_utc),
        "packet_rows": int(len(block)),
        "n_rows": int(len(block)),
        "n_pre_rows": int(len(pre)),
        "breadth_share_max_pre": None if pre.empty else float(pre["breadth_share"].max()),
        "breadth_share_mean_pre": None if pre.empty else float(pre["breadth_share"].mean()),
        "core_downside_share_max_pre": None if pre.empty else float(pre["core_downside_share"].max()),
        "core_downside_share_mean_pre": None if pre.empty else float(pre["core_downside_share"].mean()),
        "vol_complex_share_max_pre": None if pre.empty else float(pre["vol_complex_share"].max()),
        "vol_complex_share_mean_pre": None if pre.empty else float(pre["vol_complex_share"].mean()),
        "sustained_event_rate_pre": None if pre.empty else float(pre["sustained_event"].mean()),
        "raw_p_debug_max_pre": None if pre.empty else float(pre["raw_p_debug"].max()),
        "raw_p_debug_mean_pre": None if pre.empty else float(pre["raw_p_debug"].mean()),
        "cond_p_rate_pre": None if pre.empty else float(pre["cond_p"].mean()),
        "G_numerator_vol_stress_max_pre": None if pre.empty else float(pre["G_numerator_vol_stress"].max()),
        "G_denominator_core_stress_mean_pre": None if pre.empty else float(pre["G_denominator_core_stress"].mean()),
        "dominance_raw_max_pre": None if pre.empty else float(pre["dominance_raw"].max()),
        "dominance_raw_mean_pre": None if pre.empty else float(pre["dominance_raw"].mean()),
        "G_max_pre": None if pre.empty else float(pre["G"].max()),
        "G_mean_pre": None if pre.empty else float(pre["G"].mean()),
        "cond_gain_rate_pre": None if pre.empty else float(pre["cond_gain"].mean()),
        "delta_mean_pre": None if pre.empty else float(pre["delta"].mean()),
        "cond_delta_rate_pre": None if pre.empty else float(pre["cond_delta"].mean()),
        "alarm_raw_rate_pre": None if pre.empty else float(pre["alarm_raw"].mean()),
        "alarm_gated_rate_pre": None if pre.empty else float(pre["alarm_gated"].mean()),
        "longest_sustained_run_pre": 0 if pre.empty else longest_run(pre["sustained_event"]),
        "longest_alarm_raw_run_pre": 0 if pre.empty else longest_run(pre["alarm_raw"]),
        "longest_alarm_gated_run_pre": 0 if pre.empty else longest_run(pre["alarm_gated"]),
        "first_cond_p_ts_utc": iso_or_none(first_cond_p_ts),
        "first_alarm_raw_ts_utc": iso_or_none(first_alarm_raw_ts),
        "first_alarm_gated_ts_utc": iso_or_none(first_alarm_gated_ts),
        "lead_minutes_cond_p": lead_minutes_cond_p,
        "lead_minutes_alarm_raw": lead_minutes_alarm_raw,
        "lead_minutes_alarm_gated": lead_minutes_alarm_gated,
        "p_diff_abs_max": None if pre.empty else float(pre["p_diff_abs"].max()),
        "G_diff_abs_max": None if pre.empty else float(pre["G_diff_abs"].max()),
        "packet_csv": str(packet_path.relative_to(ROOT)),
        "window_start_ts_utc": iso_or_none(pd.Timestamp(block["ts_utc"].min())) if not block.empty else None,
        "window_end_ts_utc": iso_or_none(pd.Timestamp(block["ts_utc"].max())) if not block.empty else None,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    panel = pd.read_parquet(PANEL_PATH)
    market_state = build_market_state_panel(panel)
    primary = load_primary_manifest()
    control = load_control_manifest()
    backfill_control = load_backfill_control_manifest()
    scan = load_scan()

    summary_rows: list[dict[str, Any]] = []
    skipped_slices: list[str] = []
    readme_lines = [
        "# Intraday v2 ingredient packet",
        "",
        f"- scan_family: `{SCAN_FAMILY}`",
        f"- breadth_event_min_share: `{BREADTH_EVENT_MIN_SHARE}`",
        f"- min_run_length: `{MIN_RUN_LENGTH}`",
        "",
        "## Intent",
        "- compare true events vs killer controls at the raw ingredient level",
        "- inspect whether killer controls are cascade look-alikes, broad downside days, or vol-complex dominance cases",
        "",
    ]

    for focus in FOCUS_CONFIGS:
        config_id = focus["config_id"]
        config_label = focus["label"]
        scan_row = select_scan_row(scan, config_id)
        thr_json = json.dumps({
            "delta_window": int(scan_row["delta_window"]),
            "p_window": int(scan_row["p_window"]),
            "g_window": int(scan_row["g_window"]),
            "eps_g": float(scan_row["eps_g"]),
            "tau_delta": float(scan_row["tau_delta"]),
            "tau_p": float(scan_row.get("tau_p", 0.0)),
            "p_min": float(scan_row.get("p_min", 0.0)),
            "p_z_threshold": float(scan_row["p_z_threshold"]),
            "k_consec_alarm": int(scan_row["k_consec_alarm"]),
            "warmup_bars": int(scan_row["warmup_bars"]),
        }, sort_keys=True)

        readme_lines.extend([
            f"## {config_label}",
            f"- config_id: `{config_id}`",
            f"- thresholds: `{thr_json}`",
            "",
        ])

        adapter, _ = build_adapter(market_state, scan_row)
        ingredient = build_ingredient_frame(market_state, scan_row, adapter)

        for slice_id in focus["target_slices"]:
            if slice_id.startswith("covid_noncollapse") or slice_id.startswith("volmageddon_control"):
                row, control_source = maybe_select_control_row_with_backfill(control, backfill_control, slice_id)
                kind = "control"
                collapse_ts_utc = None
                if row is None:
                    skipped_slices.append(
                        f"{config_id} / {slice_id}: control_id missing from {CONTROL_MANIFEST_CSV.relative_to(ROOT)}"
                        + (
                            f" and {BACKFILL_CONTROL_MANIFEST_CSV.relative_to(ROOT)}"
                            if BACKFILL_CONTROL_MANIFEST_CSV.exists()
                            else ""
                        )
                    )
                    readme_lines.append(
                        f"- skipped slice: `{config_id} / {slice_id}` (missing control in current manifest"
                        + (
                            f" and backfill manifest `{BACKFILL_CONTROL_MANIFEST_CSV.relative_to(ROOT)}`"
                            if BACKFILL_CONTROL_MANIFEST_CSV.exists()
                            else ""
                        )
                        + ")"
                    )
                    continue
            else:
                row = maybe_select_event_row(primary, slice_id)
                kind = "event"
                if row is None:
                    skipped_slices.append(f"{config_id} / {slice_id}: event_id missing from {PRIMARY_MANIFEST_CSV.relative_to(ROOT)}")
                    readme_lines.append(f"- skipped slice: `{config_id} / {slice_id}` (missing event in current manifest)")
                    continue
                collapse_ts_utc = row["collapse_ts_utc"]

            block = ingredient.loc[
                (ingredient.index >= row["start_ts_utc"]) & (ingredient.index <= row["end_ts_utc"])
            ].copy()

            if block.empty:
                skipped_slices.append(f"{config_id} / {slice_id}: empty block after slicing {iso_or_none(pd.Timestamp(row['start_ts_utc']))} to {iso_or_none(pd.Timestamp(row['end_ts_utc']))}")
                readme_lines.append(f"- skipped slice: `{config_id} / {slice_id}` (empty sliced block)")
                continue

            block = block.reset_index().rename(columns={"index": "ts_utc"})
            block["ts_utc"] = pd.to_datetime(block["ts_utc"], utc=True, errors="raise")
            block["config_id"] = config_id
            block["config_label"] = config_label
            block["slice_id"] = slice_id
            block["kind"] = kind
            block["window_start_ts_utc"] = row["start_ts_utc"]
            block["window_end_ts_utc"] = row["end_ts_utc"]
            block["collapse_ts_utc"] = collapse_ts_utc

            packet_path = write_packet(block, config_id=config_id, slice_id=slice_id)
            readme_lines.append(f"- built packet: `{packet_path.relative_to(ROOT)}`")
            summary_rows.append(
                summarize_block(
                    block=block,
                    config_id=config_id,
                    config_label=config_label,
                    slice_id=slice_id,
                    kind=kind,
                    collapse_ts_utc=collapse_ts_utc,
                    packet_path=packet_path,
                )
            )
            readme_lines.extend([
                f"### {slice_id} ({kind})",
                f"- rows: `{len(block)}`",
                f"- start_ts_utc: `{iso_or_none(pd.Timestamp(row['start_ts_utc']))}`",
                f"- end_ts_utc: `{iso_or_none(pd.Timestamp(row['end_ts_utc']))}`",
                f"- collapse_ts_utc: `{iso_or_none(pd.Timestamp(collapse_ts_utc)) if collapse_ts_utc is not None else None}`",
                (
                    f"- control_source: `{control_source}`"
                    if kind == "control"
                    else f"- control_source: `{None}`"
                ),
                "",
            ])

    if summary_rows:
        summary = pd.DataFrame(summary_rows).sort_values(
            ["config_id", "kind", "slice_id"],
            ascending=[True, True, True],
        )
    else:
        summary = pd.DataFrame()

    summary.to_csv(OUT_SUMMARY_CSV, index=False)

    if skipped_slices:
        readme_lines.extend([
            "",
            "## Skipped slices",
        ])
        readme_lines.extend([f"- `{msg}`" for msg in skipped_slices])

    OUT_README_MD.write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

    print(f"Wrote ingredient packet to: {OUT_DIR}")
    if skipped_slices:
        print("Skipped slices:")
        for msg in skipped_slices:
            print(f"  - {msg}")
    print(OUT_SUMMARY_CSV)
    print(OUT_README_MD)


if __name__ == "__main__":
    main()
