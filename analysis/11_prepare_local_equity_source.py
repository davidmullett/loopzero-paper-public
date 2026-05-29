from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "public" / "equity_events" / "raw" / "provider_drop"
PROC_DIR = ROOT / "data" / "public" / "equity_events" / "processed"
PANEL_PARQUET_FILE = PROC_DIR / "equity_panel_1min.parquet"
PANEL_CSV_FILE = PROC_DIR / "equity_panel_1min.csv"
MANIFEST_FILE = PROC_DIR / "equity_panel_1min_manifest.json"
EVENT_FAMILY = "equity_dislocations_v1"
ET_TZ = "America/New_York"

PROVIDER_PRIORITY = ["alpaca", "manual", "stooq"]
REQUIRED_PRICE_COLUMNS = ["open", "high", "low", "close", "volume"]
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

COLUMN_ALIASES = {
    "timestamp": ["timestamp", "time", "datetime", "date", "t"],
    "open": ["open", "o"],
    "high": ["high", "h"],
    "low": ["low", "l"],
    "close": ["close", "c"],
    "volume": ["volume", "v"],
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def build_manifest_lookup(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    files = manifest.get("files", [])
    if not isinstance(files, list):
        return lookup

    for item in files:
        if not isinstance(item, dict):
            continue
        filename = str(item.get("filename", "")).strip()
        if filename:
            lookup[filename] = item
    return lookup


def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def symbol_from_filename(path: Path) -> str:
    stem = path.stem
    if stem.startswith("bars_"):
        return normalize_symbol(stem.replace("bars_", "", 1))
    return normalize_symbol(stem)


def iter_provider_manifests(provider_dir: Path) -> list[Path]:
    manifests = sorted(provider_dir.rglob("source_manifest.json"))
    if not manifests and provider_dir.exists():
        fallback = provider_dir / "source_manifest.json"
        if fallback.exists():
            manifests = [fallback]
    return manifests


def first_present(columns: list[str], aliases: list[str]) -> str | None:
    lowered = {c.lower(): c for c in columns}
    for alias in aliases:
        hit = lowered.get(alias.lower())
        if hit is not None:
            return hit
    return None


def rename_to_canonical(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    rename_map: dict[str, str] = {}
    missing: list[str] = []

    for canonical, aliases in COLUMN_ALIASES.items():
        found = first_present(list(df.columns), aliases)
        if found is None:
            missing.append(canonical)
        else:
            rename_map[found] = canonical

    if missing:
        raise ValueError(
            f"Missing required columns in {path}: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    return df.rename(columns=rename_map)


def coerce_timestamp(series: pd.Series, path: Path, timezone_assumption: str | None) -> pd.Series:
    raw = pd.to_datetime(series, errors="coerce")
    bad = int(raw.isna().sum())
    if bad > 0:
        raise ValueError(f"Found {bad} unparsable timestamps in {path}")

    tz = getattr(raw.dt, "tz", None)
    if tz is None:
        if not timezone_assumption:
            raise ValueError(
                f"Naive timestamps found in {path}, but no timezone assumption was provided "
                "in the provider source manifest."
            )
        raw = raw.dt.tz_localize(timezone_assumption)

    return raw.dt.tz_convert("UTC")


def normalize_one_file(
    path: Path,
    provider: str,
    file_meta: dict[str, Any],
    provider_manifest: dict[str, Any],
) -> tuple[pd.DataFrame | None, dict[str, Any]]:
    df = pd.read_csv(path)

    symbol = normalize_symbol(str(file_meta.get("symbol") or symbol_from_filename(path)))
    adjustment = str(file_meta.get("adjustment") or provider_manifest.get("adjustment") or "unknown")
    timezone_assumption = file_meta.get("timezone_assumption") or provider_manifest.get("timezone_assumption")

    if provider == "alpaca" and not timezone_assumption:
        timezone_assumption = "UTC"

    if df.empty:
        summary = {
            "provider": provider,
            "filename": path.name,
            "source_path": str(path.relative_to(ROOT)),
            "symbol": symbol,
            "adjustment": adjustment,
            "rows": 0,
            "start_ts_utc": None,
            "end_ts_utc": None,
            "checksum_sha256": sha256_file(path),
            "notes": file_meta.get("notes", ""),
            "skipped_reason": "empty_source_file",
        }
        return None, summary

    df = rename_to_canonical(df, path)

    ts = coerce_timestamp(df["timestamp"], path, timezone_assumption)

    out = df[["open", "high", "low", "close", "volume"]].copy()
    for col in REQUIRED_PRICE_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    bad_numeric = int(out[REQUIRED_PRICE_COLUMNS].isna().any(axis=1).sum())
    if bad_numeric > 0:
        raise ValueError(f"Found {bad_numeric} rows with invalid OHLCV values in {path}")

    out.insert(0, "ts", ts)
    out["symbol"] = symbol
    out["provider"] = provider
    out["adjustment"] = adjustment
    out["event_family"] = EVENT_FAMILY

    out = (
        out.sort_values("ts")
        .drop_duplicates(subset=["ts", "symbol", "provider"])
        .reset_index(drop=True)
    )
    out["ts_utc"] = out["ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    out["ts_et"] = out["ts"].dt.tz_convert(ET_TZ).dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    out = out[CANONICAL_COLUMNS].copy()

    summary = {
        "provider": provider,
        "filename": path.name,
        "source_path": str(path.relative_to(ROOT)),
        "symbol": symbol,
        "adjustment": adjustment,
        "rows": int(len(out)),
        "start_ts_utc": out["ts_utc"].iloc[0] if not out.empty else None,
        "end_ts_utc": out["ts_utc"].iloc[-1] if not out.empty else None,
        "checksum_sha256": sha256_file(path),
        "notes": file_meta.get("notes", ""),
    }
    return out, summary


def collect_manifest_dir_frames(
    provider: str,
    manifest_dir: Path,
) -> tuple[list[pd.DataFrame], list[dict[str, Any]]]:
    provider_manifest = load_json(manifest_dir / "source_manifest.json")
    manifest_lookup = build_manifest_lookup(provider_manifest)

    frames: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []

    csv_files = sorted(manifest_dir.glob("bars_*.csv"))

    for path in csv_files:
        if path.parent.name == "_raw_pages":
            continue
        file_meta = manifest_lookup.get(path.name, {})
        frame, summary = normalize_one_file(path, provider, file_meta, provider_manifest)
        if frame is not None and not frame.empty:
            frames.append(frame)
        summaries.append(summary)

    return frames, summaries


def collect_provider_frames(provider: str) -> tuple[list[pd.DataFrame], list[dict[str, Any]]]:
    provider_dir = RAW_ROOT / provider
    if not provider_dir.exists():
        return [], []

    frames: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []

    manifest_paths = iter_provider_manifests(provider_dir)
    if not manifest_paths:
        return [], []

    for manifest_path in manifest_paths:
        manifest_dir = manifest_path.parent
        sub_frames, sub_summaries = collect_manifest_dir_frames(provider, manifest_dir)
        frames.extend(sub_frames)
        summaries.extend(sub_summaries)

    return frames, summaries


def discover_raw_csvs() -> list[str]:
    discovered: list[str] = []
    for provider in PROVIDER_PRIORITY:
        provider_dir = RAW_ROOT / provider
        if not provider_dir.exists():
            continue
        for path in sorted(provider_dir.rglob("bars_*.csv")):
            if path.parent.name == "_raw_pages":
                continue
            discovered.append(str(path.relative_to(ROOT)))
    return discovered


def build_panel() -> tuple[pd.DataFrame | None, list[dict[str, Any]]]:
    all_frames: list[pd.DataFrame] = []
    all_summaries: list[dict[str, Any]] = []

    for provider in PROVIDER_PRIORITY:
        frames, summaries = collect_provider_frames(provider)
        all_frames.extend(frames)
        all_summaries.extend(summaries)

    if not all_frames:
        return None, all_summaries

    panel = pd.concat(all_frames, ignore_index=True)
    panel = (
        panel.sort_values(["ts_utc", "symbol", "provider"])
        .drop_duplicates(subset=["symbol", "provider", "ts_utc"])
        .reset_index(drop=True)
    )
    panel = panel[CANONICAL_COLUMNS].copy()
    return panel, all_summaries


def write_manifest(
    panel: pd.DataFrame,
    input_summaries: list[dict[str, Any]],
    panel_path: Path,
    output_format: str,
) -> None:
    manifest = {
        "event_family": EVENT_FAMILY,
        "generated_at_utc": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider_priority": PROVIDER_PRIORITY,
        "status": "ready",
        "output": {
            "panel_path": str(panel_path.relative_to(ROOT)),
            "manifest_path": str(MANIFEST_FILE.relative_to(ROOT)),
            "format": output_format,
            "rows": int(len(panel)),
            "symbols": sorted(panel["symbol"].dropna().unique().tolist()),
            "providers": sorted(panel["provider"].dropna().unique().tolist()),
            "start_ts_utc": panel["ts_utc"].min() if not panel.empty else None,
            "end_ts_utc": panel["ts_utc"].max() if not panel.empty else None,
            "columns": CANONICAL_COLUMNS,
        },
        "inputs": input_summaries,
    }

    with MANIFEST_FILE.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")


def write_pending_manifest(discovered_csvs: list[str]) -> None:
    manifest = {
        "event_family": EVENT_FAMILY,
        "generated_at_utc": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider_priority": PROVIDER_PRIORITY,
        "status": "awaiting_raw_inputs",
        "message": (
            "No raw provider CSV files were found yet. Drop one or more CSV files into "
            "alpaca/, manual/, or stooq/ and rerun this script."
        ),
        "expected_provider_dirs": [
            str((RAW_ROOT / provider).relative_to(ROOT)) for provider in PROVIDER_PRIORITY
        ],
        "discovered_csvs": discovered_csvs,
        "output": {
            "preferred_panel_path": str(PANEL_PARQUET_FILE.relative_to(ROOT)),
            "fallback_panel_path": str(PANEL_CSV_FILE.relative_to(ROOT)),
            "manifest_path": str(MANIFEST_FILE.relative_to(ROOT)),
            "rows": 0,
            "symbols": [],
            "providers": [],
            "start_ts_utc": None,
            "end_ts_utc": None,
            "columns": CANONICAL_COLUMNS,
        },
        "inputs": [],
    }

    with MANIFEST_FILE.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")


def write_panel(panel: pd.DataFrame) -> tuple[Path, str]:
    try:
        panel.to_parquet(PANEL_PARQUET_FILE, index=False)
        return PANEL_PARQUET_FILE, "parquet"
    except ImportError:
        panel.to_csv(PANEL_CSV_FILE, index=False)
        return PANEL_CSV_FILE, "csv_fallback_no_parquet_engine"


def main() -> None:
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    panel, input_summaries = build_panel()
    if panel is None:
        discovered_csvs = discover_raw_csvs()
        write_pending_manifest(discovered_csvs)
        print("No raw provider CSV files were found yet.")
        print("Expected files under one of:")
        for provider in PROVIDER_PRIORITY:
            print(f"  - {(RAW_ROOT / provider).relative_to(ROOT)}")
        print(f"Wrote pending manifest to {MANIFEST_FILE}")
        return

    panel_path, output_format = write_panel(panel)
    write_manifest(panel, input_summaries, panel_path, output_format)

    print(f"Wrote normalized equity panel to {panel_path}")
    print(f"Wrote panel manifest to {MANIFEST_FILE}")
    print(f"Output format: {output_format}")
    print(f"Rows: {len(panel)}")
    print(f"Symbols: {', '.join(sorted(panel['symbol'].unique()))}")
    print(f"Providers: {', '.join(sorted(panel['provider'].unique()))}")
    print(f"Start: {panel['ts_utc'].min()}")
    print(f"End:   {panel['ts_utc'].max()}")


if __name__ == "__main__":
    main()