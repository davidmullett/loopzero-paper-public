from __future__ import annotations

import os

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "data" / "public" / "event_catalogs" / "equity_dislocations_v1.csv"

def resolve_catalog() -> Path:
    family = os.environ.get("LZ_EVENT_FAMILY", "equity_dislocations_v1")
    family_catalog = ROOT / "data" / "public" / "event_catalogs" / f"{family}.csv"
    if family_catalog.exists():
        return family_catalog
    return DEFAULT_CATALOG

CATALOG = resolve_catalog()
PROC_DIR = ROOT / "data" / "public" / "equity_events" / "processed"
PANEL_PARQUET = PROC_DIR / "equity_panel_1min.parquet"
PANEL_CSV = PROC_DIR / "equity_panel_1min.csv"
EVENT_WINDOWS_DIR = PROC_DIR / "event_windows"
MANIFEST_DIR = ROOT / "results" / "manifests" / "equity_events"

EVENT_FAMILY = os.environ.get("LZ_EVENT_FAMILY", "equity_dislocations_v1")
ET_TZ = "America/New_York"
DEFAULT_WINDOW_END_HOUR_ET = 20

REQUIRED_COLUMNS = [
    "event_id",
    "family",
    "event_date",
    "start_ts_et",
    "collapse_ts_et",
    "collapse_rule",
    "endpoint_class",
    "endpoint_source",
    "primary_symbols",
    "context_symbols",
    "control_pool_id",
    "include_primary",
    "notes",
]

ACTIVE_REQUIRED_NONEMPTY = [
    "event_id",
    "family",
    "event_date",
    "start_ts_et",
    "collapse_ts_et",
    "collapse_rule",
    "endpoint_class",
    "endpoint_source",
    "primary_symbols",
    "include_primary",
]

PRIMARY_REQUIRED_NONEMPTY = ACTIVE_REQUIRED_NONEMPTY + ["control_pool_id"]
TIME_REQUIRED_NONEMPTY = ["start_ts_et", "collapse_ts_et"]

PRIMARY_MANIFEST_CSV = MANIFEST_DIR / f"{EVENT_FAMILY}.primary_event_manifest.csv"
PRIMARY_MANIFEST_JSON = MANIFEST_DIR / f"{EVENT_FAMILY}.primary_event_manifest.summary.json"


def init_catalog_template(overwrite: bool = False) -> None:
    """Create a header-only event catalog template using the current schema."""
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    if CATALOG.exists() and CATALOG.stat().st_size > 0 and not overwrite:
        raise FileExistsError(
            f"Catalog already exists and is non-empty: {CATALOG}. "
            "Use --overwrite to replace it."
        )
    pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(CATALOG, index=False)
    print(f"Wrote catalog template to {CATALOG}")
    print("Next: fill in at least one event row, then rerun this script without --init-catalog.")


def is_blank(value: object) -> bool:
    if pd.isna(value):
        return True
    return str(value).strip() == ""


def parse_bool(value: object) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def parse_symbol_list(value: object) -> list[str]:
    if is_blank(value):
        return []
    parts = [part.strip().upper() for part in str(value).split("|")]
    return [part for part in parts if part]


def get_active_rows(catalog: pd.DataFrame) -> pd.DataFrame:
    return catalog.loc[~catalog["event_id"].map(is_blank)].copy()


def get_primary_rows(catalog: pd.DataFrame) -> pd.DataFrame:
    active = get_active_rows(catalog)
    if active.empty:
        return active
    return active.loc[active["include_primary"].map(parse_bool)].copy()


def default_window_end_ts_utc(event_date_value: object) -> pd.Timestamp:
    date_ts = pd.to_datetime(event_date_value, errors="raise")
    local_midnight = pd.Timestamp(date_ts.date()).tz_localize(ET_TZ)
    local_end = local_midnight + pd.Timedelta(hours=DEFAULT_WINDOW_END_HOUR_ET)
    return local_end.tz_convert("UTC")


def load_catalog() -> pd.DataFrame:
    if not CATALOG.exists():
        raise FileNotFoundError(
            f"Catalog file not found: {CATALOG}\n"
            "Create it with:\n"
            "  python3 analysis/10_build_equity_event_family.py --init-catalog"
        )

    try:
        catalog = pd.read_csv(CATALOG)
    except EmptyDataError as exc:
        raise ValueError(
            f"Catalog exists but is empty: {CATALOG}\n"
            "Write at least the header row or run:\n"
            "  python3 analysis/10_build_equity_event_family.py --init-catalog --overwrite"
        ) from exc

    missing = [c for c in REQUIRED_COLUMNS if c not in catalog.columns]
    if missing:
        raise ValueError(
            "Catalog is missing required columns: "
            f"{missing}\nExpected columns:\n  {REQUIRED_COLUMNS}"
        )

    return catalog


def report_incomplete_rows(catalog: pd.DataFrame, required_fields: list[str]) -> pd.DataFrame:
    active = get_active_rows(catalog)
    if active.empty:
        return active.iloc[0:0].copy()

    missing_records = []
    for idx, row in active.iterrows():
        missing_fields = [col for col in required_fields if is_blank(row[col])]
        if missing_fields:
            missing_records.append(
                {
                    "row_number": int(idx) + 2,
                    "event_id": str(row.get("event_id", "")).strip(),
                    "missing_fields": ", ".join(missing_fields),
                }
            )

    return pd.DataFrame(missing_records)


def report_invalid_event_times(catalog: pd.DataFrame) -> pd.DataFrame:
    active = get_active_rows(catalog)
    if active.empty:
        return active.iloc[0:0].copy()

    issues: list[dict[str, Any]] = []
    for idx, row in active.iterrows():
        row_number = int(idx) + 2
        event_id = str(row.get("event_id", "")).strip()

        missing_fields = [col for col in TIME_REQUIRED_NONEMPTY if is_blank(row[col])]
        if missing_fields:
            issues.append(
                {
                    "row_number": row_number,
                    "event_id": event_id,
                    "issue": f"missing fields: {', '.join(missing_fields)}",
                }
            )
            continue

        start_ts = pd.to_datetime(row["start_ts_et"], utc=True, errors="coerce")
        collapse_ts = pd.to_datetime(row["collapse_ts_et"], utc=True, errors="coerce")
        event_date = pd.to_datetime(row["event_date"], errors="coerce")

        invalid_fields = []
        if pd.isna(start_ts):
            invalid_fields.append("start_ts_et")
        if pd.isna(collapse_ts):
            invalid_fields.append("collapse_ts_et")
        if pd.isna(event_date):
            invalid_fields.append("event_date")

        if invalid_fields:
            issues.append(
                {
                    "row_number": row_number,
                    "event_id": event_id,
                    "issue": f"invalid datetime parse: {', '.join(invalid_fields)}",
                }
            )
            continue

        if str(row["family"]).strip() != EVENT_FAMILY:
            issues.append(
                {
                    "row_number": row_number,
                    "event_id": event_id,
                    "issue": f"family must equal {EVENT_FAMILY}",
                }
            )
            continue

        if collapse_ts < start_ts:
            issues.append(
                {
                    "row_number": row_number,
                    "event_id": event_id,
                    "issue": "collapse timestamp must satisfy collapse >= start",
                }
            )
            continue

        window_end_ts = default_window_end_ts_utc(row["event_date"])
        if window_end_ts < collapse_ts:
            issues.append(
                {
                    "row_number": row_number,
                    "event_id": event_id,
                    "issue": "derived window end is earlier than collapse timestamp",
                }
            )

    return pd.DataFrame(issues)


def load_processed_panel() -> tuple[pd.DataFrame, str, Path]:
    if PANEL_PARQUET.exists():
        panel = pd.read_parquet(PANEL_PARQUET)
        return panel, "parquet", PANEL_PARQUET
    if PANEL_CSV.exists():
        panel = pd.read_csv(PANEL_CSV)
        return panel, "csv", PANEL_CSV
    raise FileNotFoundError(
        "No processed equity panel found. Expected one of:\n"
        f"  {PANEL_PARQUET}\n"
        f"  {PANEL_CSV}\n"
        "Run analysis/11_prepare_local_equity_source.py first."
    )


def validate_processed_panel(panel: pd.DataFrame) -> pd.DataFrame:
    required = [
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
    missing = [col for col in required if col not in panel.columns]
    if missing:
        raise ValueError(
            "Processed panel is missing required columns: "
            f"{missing}\nExpected columns:\n  {required}"
        )

    out = panel.copy()
    out["ts_utc"] = pd.to_datetime(out["ts_utc"], utc=True, errors="coerce")
    bad_ts = int(out["ts_utc"].isna().sum())
    if bad_ts > 0:
        raise ValueError(f"Processed panel has {bad_ts} unparsable ts_utc values")

    out["symbol"] = out["symbol"].astype(str).str.upper().str.strip()
    out = out.sort_values(["symbol", "provider", "ts_utc"]).reset_index(drop=True)
    return out


def build_symbol_role_map(primary_symbols: list[str], context_symbols: list[str]) -> dict[str, str]:
    role_map: dict[str, str] = {}
    for symbol in context_symbols:
        role_map[symbol] = "context"
    for symbol in primary_symbols:
        role_map[symbol] = "primary"
    return role_map


def build_event_slice(row: pd.Series, panel: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    event_id = str(row["event_id"]).strip()
    family = str(row["family"]).strip()
    endpoint_class = str(row["endpoint_class"]).strip()
    endpoint_source = str(row["endpoint_source"]).strip()
    collapse_rule = str(row["collapse_rule"]).strip()
    control_pool_id = str(row["control_pool_id"]).strip()
    notes = "" if is_blank(row.get("notes")) else str(row.get("notes")).strip()

    primary_symbols = parse_symbol_list(row["primary_symbols"])
    context_symbols = parse_symbol_list(row["context_symbols"])
    tracked_symbols = []
    for symbol in primary_symbols + context_symbols:
        if symbol not in tracked_symbols:
            tracked_symbols.append(symbol)

    start_ts_utc = pd.to_datetime(row["start_ts_et"], utc=True, errors="raise")
    collapse_ts_utc = pd.to_datetime(row["collapse_ts_et"], utc=True, errors="raise")
    window_end_ts_utc = default_window_end_ts_utc(row["event_date"])

    role_map = build_symbol_role_map(primary_symbols, context_symbols)

    slice_df = panel.loc[
        (panel["ts_utc"] >= start_ts_utc)
        & (panel["ts_utc"] <= window_end_ts_utc)
        & (panel["symbol"].isin(tracked_symbols))
    ].copy()

    if not slice_df.empty:
        slice_df["event_id"] = event_id
        slice_df["symbol_role"] = slice_df["symbol"].map(role_map).fillna("unclassified")
        slice_df["endpoint_class"] = endpoint_class
        slice_df["endpoint_source"] = endpoint_source
        slice_df["collapse_rule"] = collapse_rule
        slice_df["collapse_ts_utc"] = collapse_ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        slice_df = slice_df.sort_values(["symbol", "provider", "ts_utc"]).reset_index(drop=True)
    else:
        slice_df = pd.DataFrame(
            columns=list(panel.columns)
            + ["event_id", "symbol_role", "endpoint_class", "endpoint_source", "collapse_rule", "collapse_ts_utc"]
        )

    available_symbols = sorted(slice_df["symbol"].dropna().unique().tolist()) if not slice_df.empty else []
    available_primary_symbols = [symbol for symbol in primary_symbols if symbol in available_symbols]
    missing_primary_symbols = [symbol for symbol in primary_symbols if symbol not in available_primary_symbols]
    available_context_symbols = [symbol for symbol in context_symbols if symbol in available_symbols]
    missing_context_symbols = [symbol for symbol in context_symbols if symbol not in available_context_symbols]

    if len(available_primary_symbols) == 0:
        coverage_status_primary = "missing_primary"
    elif missing_primary_symbols:
        coverage_status_primary = "partial_primary"
    else:
        coverage_status_primary = "present_primary"

    if len(context_symbols) == 0:
        coverage_status_context = "not_applicable_context"
    elif len(available_context_symbols) == 0:
        coverage_status_context = "missing_context"
    elif missing_context_symbols:
        coverage_status_context = "partial_context"
    else:
        coverage_status_context = "present_context"

    n_primary_rows = int((slice_df["symbol_role"] == "primary").sum()) if not slice_df.empty else 0
    n_context_rows = int((slice_df["symbol_role"] == "context").sum()) if not slice_df.empty else 0

    slice_path = EVENT_WINDOWS_DIR / f"{event_id}.window.csv"
    EVENT_WINDOWS_DIR.mkdir(parents=True, exist_ok=True)
    slice_df.to_csv(slice_path, index=False)

    summary = {
        "event_id": event_id,
        "family": family,
        "event_date": str(row["event_date"]),
        "endpoint_class": endpoint_class,
        "endpoint_source": endpoint_source,
        "collapse_rule": collapse_rule,
        "control_pool_id": control_pool_id,
        "include_primary": True,
        "start_ts_utc": start_ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collapse_ts_utc": collapse_ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_end_ts_utc": window_end_ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "primary_symbols": "|".join(primary_symbols),
        "context_symbols": "|".join(context_symbols),
        "tracked_symbols": "|".join(tracked_symbols),
        "available_primary_symbols": "|".join(available_primary_symbols),
        "missing_primary_symbols": "|".join(missing_primary_symbols),
        "available_context_symbols": "|".join(available_context_symbols),
        "missing_context_symbols": "|".join(missing_context_symbols),
        "n_rows": int(len(slice_df)),
        "n_primary_rows": n_primary_rows,
        "n_context_rows": n_context_rows,
        "slice_path": str(slice_path.relative_to(ROOT)),
        "coverage_status_primary": coverage_status_primary,
        "coverage_status_context": coverage_status_context,
        "coverage_status": coverage_status_primary,
        "notes": notes,
    }
    return slice_df, summary


def build_primary_event_manifest(catalog: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    primary_rows = get_primary_rows(catalog)
    if primary_rows.empty:
        return primary_rows.iloc[0:0].copy()

    summaries = []
    for _, row in primary_rows.iterrows():
        _, summary = build_event_slice(row, panel)
        summaries.append(summary)

    manifest = pd.DataFrame(summaries)
    keep_cols = [
        "event_id",
        "family",
        "event_date",
        "endpoint_class",
        "endpoint_source",
        "collapse_rule",
        "control_pool_id",
        "include_primary",
        "start_ts_utc",
        "collapse_ts_utc",
        "window_end_ts_utc",
        "primary_symbols",
        "context_symbols",
        "tracked_symbols",
        "available_primary_symbols",
        "missing_primary_symbols",
        "available_context_symbols",
        "missing_context_symbols",
        "n_rows",
        "n_primary_rows",
        "n_context_rows",
        "slice_path",
        "coverage_status_primary",
        "coverage_status_context",
        "coverage_status",
        "notes",
    ]
    return manifest[keep_cols].sort_values(["event_date", "event_id"]).reset_index(drop=True)


def write_primary_manifest(manifest: pd.DataFrame) -> Path:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(PRIMARY_MANIFEST_CSV, index=False)
    return PRIMARY_MANIFEST_CSV


def write_primary_manifest_summary(
    manifest: pd.DataFrame,
    panel_format: str,
    panel_path: Path,
    catalog: pd.DataFrame,
) -> Path:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    active_rows = get_active_rows(catalog)
    primary_rows = get_primary_rows(catalog)
    excluded_rows = active_rows.loc[~active_rows["include_primary"].map(parse_bool)].copy()

    present_primary = manifest.loc[manifest["coverage_status_primary"] == "present_primary"] if not manifest.empty else manifest
    partial_primary = manifest.loc[manifest["coverage_status_primary"] == "partial_primary"] if not manifest.empty else manifest
    missing_primary = manifest.loc[manifest["coverage_status_primary"] == "missing_primary"] if not manifest.empty else manifest

    summary = {
        "event_family": EVENT_FAMILY,
        "n_catalog_rows": int(len(catalog)),
        "n_active_rows": int(len(active_rows)),
        "n_primary_rows": int(len(primary_rows)),
        "n_excluded_rows": int(len(excluded_rows)),
        "excluded_event_ids": excluded_rows["event_id"].astype(str).tolist(),
        "panel_source_format": panel_format,
        "panel_source_path": str(panel_path.relative_to(ROOT)),
        "n_events_present_primary": int(len(present_primary)) if not manifest.empty else 0,
        "n_events_partial_primary": int(len(partial_primary)) if not manifest.empty else 0,
        "n_events_missing_primary": int(len(missing_primary)) if not manifest.empty else 0,
        "event_ids_present_primary": present_primary["event_id"].astype(str).tolist() if not manifest.empty else [],
        "event_ids_partial_primary": partial_primary["event_id"].astype(str).tolist() if not manifest.empty else [],
        "event_ids_missing_primary": missing_primary["event_id"].astype(str).tolist() if not manifest.empty else [],
        "n_events_with_rows": int(len(manifest.loc[manifest["coverage_status_primary"] != "missing_primary"])) if not manifest.empty else 0,
        "n_events_without_rows": int(len(missing_primary)) if not manifest.empty else 0,
        "event_ids_with_rows": manifest.loc[manifest["coverage_status_primary"] != "missing_primary", "event_id"].astype(str).tolist() if not manifest.empty else [],
        "event_ids_without_rows": missing_primary["event_id"].astype(str).tolist() if not manifest.empty else [],
        "min_start_ts_utc": None if manifest.empty else str(manifest["start_ts_utc"].min()),
        "max_window_end_ts_utc": None if manifest.empty else str(manifest["window_end_ts_utc"].max()),
        "controls_status": "pending_not_yet_implemented",
    }

    PRIMARY_MANIFEST_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return PRIMARY_MANIFEST_JSON


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--init-catalog",
        action="store_true",
        help="Create a header-only event catalog template and exit.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow --init-catalog to overwrite an existing non-empty catalog.",
    )
    args = parser.parse_args()

    PROC_DIR.mkdir(parents=True, exist_ok=True)
    EVENT_WINDOWS_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    if args.init_catalog:
        init_catalog_template(overwrite=args.overwrite)
        return

    catalog = load_catalog()
    print(f"Loaded catalog with {len(catalog)} rows")

    active_rows = get_active_rows(catalog)
    primary_rows = get_primary_rows(catalog)
    print(f"Active rows: {len(active_rows)}")
    print(f"Primary rows: {len(primary_rows)}")

    if catalog.empty or active_rows.empty:
        print("Catalog is valid but contains no active event rows yet.")
        print("Add at least one active event to data/public/event_catalogs/equity_dislocations_v1.csv and rerun.")
        return

    incomplete_active = report_incomplete_rows(catalog, ACTIVE_REQUIRED_NONEMPTY)
    if not incomplete_active.empty:
        print("Active catalog rows are incomplete.")
        print(incomplete_active.to_string(index=False))
        return

    incomplete_primary = report_incomplete_rows(primary_rows, PRIMARY_REQUIRED_NONEMPTY)
    if not incomplete_primary.empty:
        print("Primary rows are missing fields required for event-family building.")
        print(incomplete_primary.to_string(index=False))
        return

    time_issues = report_invalid_event_times(catalog)
    if not time_issues.empty:
        print("Catalog rows still need valid externally anchored event times.")
        print(time_issues.to_string(index=False))
        return

    panel, panel_format, panel_path = load_processed_panel()
    panel = validate_processed_panel(panel)
    print(f"Loaded processed panel from {panel_path} ({panel_format}) with {len(panel)} rows")

    manifest = build_primary_event_manifest(catalog, panel)
    manifest_path = write_primary_manifest(manifest)
    summary_path = write_primary_manifest_summary(manifest, panel_format, panel_path, catalog)

    print(f"Wrote primary event manifest to {manifest_path}")
    print(f"Wrote primary event summary JSON to {summary_path}")
    print(f"Wrote event window slices to {EVENT_WINDOWS_DIR}")
    if not manifest.empty:
        print(
            "Events with primary coverage: "
            f"{(manifest['coverage_status_primary'] != 'missing_primary').sum()} / {len(manifest)}"
        )
        print("Ready for the next phase: add real event windows, then implement controls and benchmarks.")
    else:
        print("No primary rows were available for manifest generation.")


if __name__ == "__main__":
    main()
