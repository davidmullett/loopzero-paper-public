from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INGREDIENT_DIR = ROOT / "results" / "rendered" / "equity_dislocation_family" / "intraday_v2_ingredient_packet"
OUT_DIR = ROOT / "results" / "rendered" / "comparators"
OUT_CSV = OUT_DIR / "markets_comparator_input_v2.csv"
OUT_UNIT_SUMMARY_CSV = OUT_DIR / "markets_comparator_input_v2_unit_summary.csv"
MANIFEST_CSV = OUT_DIR / "comparator_input_manifest_v1.csv"

EVENT_SLICE_IDS = {
    "volmageddon_2018_xiv",
    "covid_mwcb_2020_03_18",
}

CANONICAL_CONFIG_ID = "cfg_001339"

DEFAULT_SIGNAL_PRIORITY = ["G", "delta", "raw_p_debug", "p_v7_ttl"]
DEFAULT_SEGMENT_MINUTES = 120
MIN_SEGMENT_ROWS = 60


@dataclass(frozen=True)
class SignalChoice:
    source_col: str
    transform_name: str


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _env_str(name: str, default: str) -> str:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip()


def discover_packet_paths() -> list[Path]:
    candidates = sorted(INGREDIENT_DIR.glob("cfg_*__.packet.csv")) or sorted(INGREDIENT_DIR.glob("*.packet.csv"))
    canonical: list[Path] = []
    skipped_noncanonical: list[Path] = []

    for path in candidates:
        try:
            config_id, _ = parse_config_and_slice(path)
        except ValueError:
            skipped_noncanonical.append(path)
            continue

        if config_id == CANONICAL_CONFIG_ID:
            canonical.append(path)
        else:
            skipped_noncanonical.append(path)

    if canonical:
        return canonical

    raise FileNotFoundError(
        "No canonical ingredient packets found under "
        f"{INGREDIENT_DIR} for CANONICAL_CONFIG_ID={CANONICAL_CONFIG_ID}. "
        f"Found {len(candidates)} packet candidate(s), but none matched the canonical config."
    )


def parse_config_and_slice(path: Path) -> tuple[str, str]:
    stem = path.name
    if stem.endswith(".packet.csv"):
        stem = stem[: -len(".packet.csv")]
    if "__" not in stem:
        raise ValueError(f"Could not parse config/slice from {path}")
    config_id, slice_id = stem.split("__", 1)
    return config_id, slice_id


def classify_kind(slice_id: str) -> str:
    return "event" if slice_id in EVENT_SLICE_IDS else "control"


def choose_signal_column(df: pd.DataFrame) -> SignalChoice:
    preferred = _env_str("LZ_MARKETS_SIGNAL_COL", "").strip()
    if preferred:
        if preferred not in df.columns:
            raise ValueError(f"Requested LZ_MARKETS_SIGNAL_COL={preferred} not found in packet columns")
        return _choice_for_column(preferred)

    for col in DEFAULT_SIGNAL_PRIORITY:
        if col in df.columns:
            return _choice_for_column(col)

    raise ValueError(
        "No supported signal column found. Expected one of: "
        + ", ".join(DEFAULT_SIGNAL_PRIORITY)
    )


def _choice_for_column(col: str) -> SignalChoice:
    if col == "G":
        return SignalChoice(source_col="G", transform_name="log1p_gain")
    if col == "delta":
        return SignalChoice(source_col="delta", transform_name="one_minus_delta")
    if col == "raw_p_debug":
        return SignalChoice(source_col="raw_p_debug", transform_name="identity")
    if col == "p_v7_ttl":
        return SignalChoice(source_col="p_v7_ttl", transform_name="identity")
    return SignalChoice(source_col=col, transform_name="identity")


def transform_signal(series: pd.Series, choice: SignalChoice) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").astype(float)

    if choice.transform_name == "log1p_gain":
        s = s.replace([np.inf, -np.inf], np.nan).clip(lower=0)
        return np.log1p(s)

    if choice.transform_name == "one_minus_delta":
        s = s.replace([np.inf, -np.inf], np.nan)
        return 1.0 - s

    return s.replace([np.inf, -np.inf], np.nan)


def normalize_time_column(df: pd.DataFrame) -> pd.Series:
    if "ts_utc" not in df.columns:
        raise ValueError("Expected ts_utc column in ingredient packet")
    ts = pd.to_datetime(df["ts_utc"], utc=True, errors="coerce")
    if ts.isna().all():
        raise ValueError("ts_utc could not be parsed to datetimes")
    return ts


def infer_collapse_ts(ts: pd.Series, slice_id: str, kind: str) -> pd.Timestamp:
    if kind == "event":
        return ts.max()
    return ts.max()


def segment_frame(df: pd.DataFrame, segment_minutes: int, min_segment_rows: int) -> list[pd.DataFrame]:
    if segment_minutes <= 0:
        return [df.copy()]

    work = df.sort_values("ts_utc").reset_index(drop=True).copy()
    t0 = work["ts_utc"].min()
    delta_min = (work["ts_utc"] - t0).dt.total_seconds() / 60.0
    work["_segment_id"] = (delta_min // segment_minutes).astype(int)

    segments: list[pd.DataFrame] = []
    for _, g in work.groupby("_segment_id", sort=True):
        if len(g) < min_segment_rows:
            continue
        segments.append(g.drop(columns=["_segment_id"]).reset_index(drop=True))

    if not segments:
        return [df.sort_values("ts_utc").reset_index(drop=True).copy()]
    return segments


def build_unit_rows(path: Path, segment_minutes: int, min_segment_rows: int) -> tuple[list[pd.DataFrame], list[dict]]:
    config_id, slice_id = parse_config_and_slice(path)
    if config_id != CANONICAL_CONFIG_ID:
        return [], []
    kind = classify_kind(slice_id)

    raw = pd.read_csv(path)
    choice = choose_signal_column(raw)
    ts = normalize_time_column(raw)
    signal = transform_signal(raw[choice.source_col], choice)

    base = pd.DataFrame(
        {
            "domain_family": "markets",
            "instantiation": "volmageddon_covid_public_v2",
            "config_id": config_id,
            "slice_id": slice_id,
            "kind": kind,
            "ts_utc": ts,
            "s_t": signal,
            "signal_source_col": choice.source_col,
            "signal_transform": choice.transform_name,
            "source_csv": str(path.relative_to(ROOT)),
        }
    ).dropna(subset=["ts_utc", "s_t"])

    if base.empty:
        return [], []

    collapse_ts = infer_collapse_ts(base["ts_utc"], slice_id=slice_id, kind=kind)
    base["collapse_ts_utc"] = collapse_ts.strftime("%Y-%m-%dT%H:%M:%SZ")

    unit_frames: list[pd.DataFrame] = []
    summary_rows: list[dict] = []

    for segment_idx, seg in enumerate(segment_frame(base, segment_minutes, min_segment_rows), start=1):
        segment_id = f"seg_{segment_idx:02d}"
        unit_id = f"{config_id}__{slice_id}__{segment_id}"
        seg = seg.copy()
        seg["unit_id"] = unit_id
        seg["parent_slice_unit_id"] = f"{config_id}__{slice_id}"
        seg["segment_id"] = segment_id
        seg["segment_start_ts_utc"] = seg["ts_utc"].min().strftime("%Y-%m-%dT%H:%M:%SZ")
        seg["segment_end_ts_utc"] = seg["ts_utc"].max().strftime("%Y-%m-%dT%H:%M:%SZ")
        unit_frames.append(seg)

        summary_rows.append(
            {
                "unit_id": unit_id,
                "parent_slice_unit_id": f"{config_id}__{slice_id}",
                "config_id": config_id,
                "slice_id": slice_id,
                "kind": kind,
                "segment_id": segment_id,
                "signal_source_col": choice.source_col,
                "signal_transform": choice.transform_name,
                "n_rows": int(len(seg)),
                "segment_start_ts_utc": seg["segment_start_ts_utc"].iloc[0],
                "segment_end_ts_utc": seg["segment_end_ts_utc"].iloc[0],
                "s_t_mean": float(seg["s_t"].mean()),
                "s_t_std": float(seg["s_t"].std(ddof=0)),
                "s_t_min": float(seg["s_t"].min()),
                "s_t_p25": float(seg["s_t"].quantile(0.25)),
                "s_t_median": float(seg["s_t"].median()),
                "s_t_p75": float(seg["s_t"].quantile(0.75)),
                "s_t_max": float(seg["s_t"].max()),
                "source_csv": str(path.relative_to(ROOT)),
            }
        )

    return unit_frames, summary_rows


def ensure_manifest_row(manifest: pd.DataFrame) -> pd.DataFrame:
    required = {
        "domain_family": "markets",
        "instantiation": "volmageddon_covid_public_v2",
        "input_csv": "",
        "unit_id_col": "unit_id",
        "kind_col": "kind",
        "time_col": "ts_utc",
        "collapse_time_col": "collapse_ts_utc",
        "signal_col": "s_t",
        "notes": "",
    }

    mask = (
        manifest["domain_family"].astype(str).eq(required["domain_family"])
        & manifest["instantiation"].astype(str).eq(required["instantiation"])
    )
    if mask.any():
        return manifest

    return pd.concat([manifest, pd.DataFrame([required])], ignore_index=True)


def main() -> None:
    segment_minutes = _env_int("LZ_MARKETS_SEGMENT_MINUTES", DEFAULT_SEGMENT_MINUTES)
    min_segment_rows = _env_int("LZ_MARKETS_MIN_SEGMENT_ROWS", MIN_SEGMENT_ROWS)

    paths = discover_packet_paths()
    print(f"Using canonical comparator source config only: {CANONICAL_CONFIG_ID}")
    if not paths:
        raise FileNotFoundError(f"No ingredient packets found under {INGREDIENT_DIR}")

    all_unit_frames: list[pd.DataFrame] = []
    summary_rows: list[dict] = []
    signal_columns_used: set[str] = set()
    transform_names_used: set[str] = set()

    for path in paths:
        unit_frames, unit_summary = build_unit_rows(
            path,
            segment_minutes=segment_minutes,
            min_segment_rows=min_segment_rows,
        )
        if not unit_frames:
            continue
        all_unit_frames.extend(unit_frames)
        summary_rows.extend(unit_summary)
        signal_columns_used.update({row["signal_source_col"] for row in unit_summary})
        transform_names_used.update({row["signal_transform"] for row in unit_summary})

    if not all_unit_frames:
        raise ValueError("No rows were produced for markets comparator input v2")

    out = pd.concat(all_unit_frames, ignore_index=True)
    out = out[
        [
            "domain_family",
            "instantiation",
            "unit_id",
            "parent_slice_unit_id",
            "config_id",
            "slice_id",
            "kind",
            "segment_id",
            "segment_start_ts_utc",
            "segment_end_ts_utc",
            "ts_utc",
            "collapse_ts_utc",
            "s_t",
            "signal_source_col",
            "signal_transform",
            "source_csv",
        ]
    ].sort_values(["unit_id", "ts_utc"]).reset_index(drop=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    pd.DataFrame(summary_rows).sort_values(["config_id", "slice_id", "segment_id"]).to_csv(
        OUT_UNIT_SUMMARY_CSV,
        index=False,
    )

    if MANIFEST_CSV.exists():
        manifest = pd.read_csv(MANIFEST_CSV, dtype=str).fillna("")
    else:
        manifest = pd.DataFrame(
            columns=[
                "domain_family",
                "instantiation",
                "input_csv",
                "unit_id_col",
                "kind_col",
                "time_col",
                "collapse_time_col",
                "signal_col",
                "notes",
            ]
        )

    manifest = ensure_manifest_row(manifest)
    mask = (
        manifest["domain_family"].astype(str).eq("markets")
        & manifest["instantiation"].astype(str).eq("volmageddon_covid_public_v2")
    )
    manifest.loc[mask, "input_csv"] = str(OUT_CSV.relative_to(ROOT))
    manifest.loc[mask, "unit_id_col"] = "unit_id"
    manifest.loc[mask, "kind_col"] = "kind"
    manifest.loc[mask, "time_col"] = "ts_utc"
    manifest.loc[mask, "collapse_time_col"] = "collapse_ts_utc"
    manifest.loc[mask, "signal_col"] = "s_t"
    manifest.loc[mask, "notes"] = (
        "segmented markets comparator input v2; "
        f"canonical_config_id={CANONICAL_CONFIG_ID}; "
        "one underlying market segment = one comparator unit; "
        "noncanonical Loopzero configs excluded to avoid duplicated session units; "
        f"segment_minutes={segment_minutes}; "
        f"min_segment_rows={min_segment_rows}; "
        f"signal_source_cols={sorted(signal_columns_used)}; "
        f"signal_transforms={sorted(transform_names_used)}"
    )
    manifest.to_csv(MANIFEST_CSV, index=False)

    print(OUT_CSV)
    print(OUT_UNIT_SUMMARY_CSV)
    print(MANIFEST_CSV)
    print()
    print("canonical_config_id:", CANONICAL_CONFIG_ID)
    print("signal_source_cols:", sorted(signal_columns_used))
    print("signal_transforms:", sorted(transform_names_used))
    print("segment_minutes:", segment_minutes)
    print("min_segment_rows:", min_segment_rows)
    print("n_unique_units:", out["unit_id"].nunique())
    print("n_parent_slice_units:", out["parent_slice_unit_id"].nunique())
    print()
    print(out.head(10).to_string(index=False))


if __name__ == "__main__":
    main()