from __future__ import annotations

import os

import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVENT_FAMILY = os.environ.get("LZ_EVENT_FAMILY", "equity_dislocations_v1")
DEFAULT_CONTROL_CATALOG = ROOT / "data" / "public" / "event_catalogs" / "equity_dislocation_controls_v2.csv"

def resolve_control_catalog() -> Path:
    suffix = EVENT_FAMILY.replace("equity_dislocations_", "")
    family_control_catalog = ROOT / "data" / "public" / "event_catalogs" / f"equity_dislocation_controls_{suffix}.csv"
    if family_control_catalog.exists():
        return family_control_catalog
    return DEFAULT_CONTROL_CATALOG

CONTROL_CATALOG = resolve_control_catalog()
PANEL_PARQUET = ROOT / "data" / "public" / "equity_events" / "processed" / "equity_panel_1min.parquet"
PANEL_CSV = ROOT / "data" / "public" / "equity_events" / "processed" / "equity_panel_1min.csv"
CONTROL_WINDOWS_DIR = ROOT / "data" / "public" / "equity_events" / "processed" / "control_windows"
MANIFEST_DIR = ROOT / "results" / "manifests" / "equity_events"
CONTROL_MANIFEST_CSV = MANIFEST_DIR / f"{EVENT_FAMILY}.control_manifest.csv"
CONTROL_MANIFEST_SUMMARY_JSON = MANIFEST_DIR / f"{EVENT_FAMILY}.control_manifest.summary.json"
ET_TZ = "America/New_York"

REQUIRED_CONTROL_COLUMNS = [
    "control_id",
    "matched_to_event_id",
    "event_date",
    "start_ts_et",
    "end_ts_et",
    "control_type",
    "selection_rule",
    "include_control",
    "notes",
]

CANONICAL_COLUMNS = [
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


def load_control_catalog() -> pd.DataFrame:
    if not CONTROL_CATALOG.exists():
        raise FileNotFoundError(
            f"Missing control catalog: {CONTROL_CATALOG}\n"
            "Create data/public/event_catalogs/equity_dislocation_controls_v1.csv first."
        )

    catalog = pd.read_csv(CONTROL_CATALOG)
    missing = [col for col in REQUIRED_CONTROL_COLUMNS if col not in catalog.columns]
    if missing:
        raise ValueError(
            f"Control catalog is missing required columns: {missing}\n"
            f"Expected columns: {REQUIRED_CONTROL_COLUMNS}"
        )

    catalog["include_control"] = catalog["include_control"].map(
        lambda value: str(value).strip().lower() in {"1", "true", "yes", "y"}
    )
    catalog = catalog.copy()
    catalog["event_date"] = catalog["event_date"].astype(str)
    return catalog


def load_panel() -> tuple[pd.DataFrame, str, Path]:
    if PANEL_PARQUET.exists():
        panel = pd.read_parquet(PANEL_PARQUET)
        panel_path = PANEL_PARQUET
        panel_format = "parquet"
    elif PANEL_CSV.exists():
        panel = pd.read_csv(PANEL_CSV)
        panel_path = PANEL_CSV
        panel_format = "csv"
    else:
        raise FileNotFoundError(
            "No processed equity panel found. Expected one of:\n"
            f"  - {PANEL_PARQUET}\n"
            f"  - {PANEL_CSV}"
        )

    missing = [col for col in CANONICAL_COLUMNS if col not in panel.columns]
    if missing:
        raise ValueError(
            f"Processed panel is missing required columns: {missing}. "
            f"Available columns: {list(panel.columns)}"
        )

    panel = panel.copy()
    panel["ts_utc"] = pd.to_datetime(panel["ts_utc"], utc=True, errors="raise")
    panel["ts_et"] = panel["ts_utc"].dt.tz_convert(ET_TZ)
    panel = panel.sort_values(["ts_utc", "symbol", "provider"]).reset_index(drop=True)
    return panel, panel_format, panel_path


def build_control_slice(row: pd.Series, panel: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    control_id = str(row["control_id"])
    matched_to_event_id = str(row["matched_to_event_id"])
    event_date = str(row["event_date"])
    control_type = str(row["control_type"])
    selection_rule = str(row["selection_rule"])
    notes = str(row.get("notes", ""))

    start_ts_et = pd.Timestamp(str(row["start_ts_et"]))
    end_ts_et = pd.Timestamp(str(row["end_ts_et"]))

    if start_ts_et.tzinfo is None or end_ts_et.tzinfo is None:
        raise ValueError(
            f"Control window timestamps must be timezone-aware for control_id={control_id}. "
            f"Got start_ts_et={start_ts_et!r}, end_ts_et={end_ts_et!r}"
        )

    start_ts_utc = start_ts_et.tz_convert("UTC")
    end_ts_utc = end_ts_et.tz_convert("UTC")

    mask = (panel["ts_utc"] >= start_ts_utc) & (panel["ts_utc"] < end_ts_utc)
    slice_df = panel.loc[mask].copy()

    slice_df["control_id"] = control_id
    slice_df["matched_to_event_id"] = matched_to_event_id
    slice_df["control_type"] = control_type
    slice_df["selection_rule"] = selection_rule
    slice_df["window_start_ts_utc"] = start_ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    slice_df["window_end_ts_utc"] = end_ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    available_symbols = sorted(slice_df["symbol"].dropna().unique().tolist()) if not slice_df.empty else []

    slice_path = CONTROL_WINDOWS_DIR / f"{control_id}.window.csv"
    CONTROL_WINDOWS_DIR.mkdir(parents=True, exist_ok=True)
    slice_df.to_csv(slice_path, index=False)

    coverage_status = "present_control" if not slice_df.empty else "missing_control"

    summary = {
        "control_id": control_id,
        "matched_to_event_id": matched_to_event_id,
        "event_date": event_date,
        "control_type": control_type,
        "selection_rule": selection_rule,
        "include_control": True,
        "start_ts_utc": start_ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_ts_utc": end_ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "available_symbols": "|".join(available_symbols),
        "n_rows": int(len(slice_df)),
        "n_symbols": int(len(available_symbols)),
        "slice_path": str(slice_path.relative_to(ROOT)),
        "coverage_status": coverage_status,
        "notes": notes,
    }
    return slice_df, summary


def build_control_manifest(catalog: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    included = catalog.loc[catalog["include_control"]].copy().reset_index(drop=True)
    summaries: list[dict[str, Any]] = []

    for _, row in included.iterrows():
        _, summary = build_control_slice(row, panel)
        summaries.append(summary)

    manifest = pd.DataFrame(summaries)
    if manifest.empty:
        return manifest

    keep_cols = [
        "control_id",
        "matched_to_event_id",
        "event_date",
        "control_type",
        "selection_rule",
        "include_control",
        "start_ts_utc",
        "end_ts_utc",
        "available_symbols",
        "n_rows",
        "n_symbols",
        "slice_path",
        "coverage_status",
        "notes",
    ]
    return manifest[keep_cols].copy()


def write_control_manifest_summary(
    *,
    catalog: pd.DataFrame,
    manifest: pd.DataFrame,
    panel_format: str,
    panel_path: Path,
) -> None:
    included = catalog.loc[catalog["include_control"]].copy().reset_index(drop=True)
    excluded = catalog.loc[~catalog["include_control"]].copy().reset_index(drop=True)

    present_controls = manifest.loc[manifest["coverage_status"] == "present_control"] if not manifest.empty else manifest
    missing_controls = manifest.loc[manifest["coverage_status"] == "missing_control"] if not manifest.empty else manifest

    summary = {
        "event_family": EVENT_FAMILY,
        "n_catalog_rows": int(len(catalog)),
        "n_included_controls": int(len(included)),
        "n_excluded_controls": int(len(excluded)),
        "excluded_control_ids": excluded["control_id"].astype(str).tolist() if not excluded.empty else [],
        "panel_source_format": panel_format,
        "panel_source_path": str(panel_path.relative_to(ROOT)),
        "n_controls_present": int(len(present_controls)) if not manifest.empty else 0,
        "n_controls_missing": int(len(missing_controls)) if not manifest.empty else 0,
        "control_ids_present": present_controls["control_id"].astype(str).tolist() if not manifest.empty else [],
        "control_ids_missing": missing_controls["control_id"].astype(str).tolist() if not manifest.empty else [],
        "min_start_ts_utc": None if manifest.empty else str(manifest["start_ts_utc"].min()),
        "max_end_ts_utc": None if manifest.empty else str(manifest["end_ts_utc"].max()),
    }

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    CONTROL_MANIFEST_SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    catalog = load_control_catalog()
    active_rows = catalog.loc[catalog["include_control"]].copy().reset_index(drop=True)
    panel, panel_format, panel_path = load_panel()

    print(f"Loaded control catalog with {len(catalog)} rows")
    print(f"Included control rows: {len(active_rows)}")
    print(f"Loaded processed panel from {panel_path} ({panel_format}) with {len(panel)} rows")

    manifest = build_control_manifest(catalog, panel)

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    CONTROL_WINDOWS_DIR.mkdir(parents=True, exist_ok=True)

    if manifest.empty:
        manifest = pd.DataFrame(
            columns=[
                "control_id",
                "matched_to_event_id",
                "event_date",
                "control_type",
                "selection_rule",
                "include_control",
                "start_ts_utc",
                "end_ts_utc",
                "available_symbols",
                "n_rows",
                "n_symbols",
                "slice_path",
                "coverage_status",
                "notes",
            ]
        )

    manifest.to_csv(CONTROL_MANIFEST_CSV, index=False)
    write_control_manifest_summary(
        catalog=catalog,
        manifest=manifest,
        panel_format=panel_format,
        panel_path=panel_path,
    )

    print(f"Wrote control manifest to {CONTROL_MANIFEST_CSV}")
    print(f"Wrote control summary JSON to {CONTROL_MANIFEST_SUMMARY_JSON}")

    if not manifest.empty:
        print(f"Controls with coverage: {(manifest['coverage_status'] == 'present_control').sum()} / {len(manifest)}")
        print("Ready for the next phase: control-calibrated benchmarks and equal-FP selection.")
    else:
        print("No included control rows were available for manifest generation.")


if __name__ == "__main__":
    main()