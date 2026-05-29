from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

LATEST_PTR = ROOT / "results" / "frozen" / "comparators" / "markets_comparator_merged_state_v2__LATEST.txt"
FALLBACK_FREEZE_DIR = ROOT / "results" / "frozen" / "comparators" / "markets_comparator_merged_state_v2"

OUT_CSV = ROOT / "results" / "rendered" / "comparators" / "markets_comparator_paper_table_v1.csv"
OUT_MD = ROOT / "results" / "rendered" / "comparators" / "markets_comparator_paper_table_v1.md"

TARGET_INSTANTIATION = "volmageddon_covid_public_v2"


def resolve_freeze_dir() -> Path:
    if LATEST_PTR.exists():
        rel = LATEST_PTR.read_text(encoding="utf-8").strip()
        if rel:
            path = ROOT / rel
            if path.exists():
                return path
    if FALLBACK_FREEZE_DIR.exists():
        return FALLBACK_FREEZE_DIR
    raise FileNotFoundError("Could not resolve frozen merged comparator state v2 directory")


def load_single_row_csv(path: Path) -> pd.Series:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    if len(df) != 1:
        raise ValueError(f"Expected exactly one row in {path}")
    return df.iloc[0]


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def as_float(x) -> float | None:
    try:
        v = float(x)
        if pd.isna(v):
            return None
        return v
    except Exception:
        return None


def fmt_float(x) -> str:
    v = as_float(x)
    return "" if v is None else f"{v:.6f}"


def fmt_alarm_frac(num, den) -> str:
    n = as_float(num)
    d = as_float(den)
    if n is None or d is None:
        return ""
    return f"{int(round(n))}/{int(round(d))}"


def split_semicolon_field(value: str) -> list[str]:
    s = str(value).strip()
    if not s:
        return []
    return [part.strip() for part in s.split(";") if part.strip()]


def require_columns(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in {label}: {missing}")


def build_row(row_order: int, row_label: str, detector_family: str, config_id: str, fp_cal, n_control_alarm_units, n_control_units, n_event_alarm_units, n_event_units, distance_to_band, interpretation: str) -> dict:
    return {
        "row_order": row_order,
        "row_label": row_label,
        "detector_family": detector_family,
        "config_id": config_id,
        "fp_cal": as_float(fp_cal),
        "control_alarm_units": int(round(as_float(n_control_alarm_units))) if as_float(n_control_alarm_units) is not None else pd.NA,
        "control_units_total": int(round(as_float(n_control_units))) if as_float(n_control_units) is not None else pd.NA,
        "control_alarm_fraction": fmt_alarm_frac(n_control_alarm_units, n_control_units),
        "event_alarm_units": int(round(as_float(n_event_alarm_units))) if as_float(n_event_alarm_units) is not None else pd.NA,
        "event_units_total": int(round(as_float(n_event_units))) if as_float(n_event_units) is not None else pd.NA,
        "event_alarm_fraction": fmt_alarm_frac(n_event_alarm_units, n_event_units),
        "distance_to_band": as_float(distance_to_band),
        "interpretation": interpretation,
    }


def lookup_config(df: pd.DataFrame, detector_family: str, config_id: str) -> pd.Series:
    hit = df[
        df["detector_family"].astype(str).eq(detector_family)
        & df["config_id"].astype(str).eq(config_id)
    ].copy()
    if hit.empty:
        raise ValueError(f"Could not find detector_family={detector_family}, config_id={config_id}")
    if len(hit) > 1:
        hit = hit.sort_values("config_id", kind="stable")
    return hit.iloc[0]


def build_markdown_table(df: pd.DataFrame, freeze_dir: Path) -> str:
    lines = [
        "# Markets comparator paper table v1",
        "",
        f"Paper-facing comparator summary derived strictly from frozen merged comparator state v2: `{freeze_dir.relative_to(ROOT)}`.",
        "",
        "| Row | Family | Config | FP | Control alarms | Event alarms | Distance to band | Interpretation |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for _, r in df.iterrows():
        lines.append(
            "| "
            + f"{r['row_label']} | "
            + f"{r['detector_family']} | "
            + f"{r['config_id']} | "
            + f"{fmt_float(r['fp_cal'])} | "
            + f"{r['control_alarm_fraction']} | "
            + f"{r['event_alarm_fraction']} | "
            + f"{fmt_float(r['distance_to_band'])} | "
            + f"{r['interpretation']} |"
        )

    lines.extend(
        [
            "",
            "## Reading note",
            "- `Control alarms` reports alarmed control units over total control units.",
            "- `Event alarms` reports alarmed event units over total event units.",
            "- `Distance to band` is the absolute amount by which the config misses the locked equal-FP interval `[0.03, 0.07]`.",
            "- The slow-family numeric nearest row is separated from the best nontrivial slow-family row to avoid conflating trivial silence with a meaningful near miss.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    freeze_dir = resolve_freeze_dir()

    merged_summary = load_single_row_csv(freeze_dir / "markets_comparator_merged_summary_v2.csv")
    acceptance = load_csv(freeze_dir / "comparator_acceptance_matrix_v1.csv")
    slow_fullgrid = load_csv(freeze_dir / "markets_slow_comparator_calibration_fullgrid_v1.csv")

    require_columns(
        acceptance,
        [
            "instantiation",
            "detector_family",
            "config_id",
            "fp_cal",
            "n_control_alarm_units",
            "n_control_units_cal",
            "n_event_alarm_units",
            "n_event_units_cal",
            "distance_to_band",
        ],
        "comparator_acceptance_matrix_v1.csv",
    )
    require_columns(
        slow_fullgrid,
        [
            "instantiation",
            "detector_family",
            "config_id",
            "fp_cal",
            "n_control_alarm_units",
            "n_control_units_cal",
            "n_event_alarm_units",
            "n_event_units_cal",
            "distance_to_band",
        ],
        "markets_slow_comparator_calibration_fullgrid_v1.csv",
    )

    acceptance = acceptance[acceptance["instantiation"].astype(str).eq(TARGET_INSTANTIATION)].copy()
    slow_fullgrid = slow_fullgrid[slow_fullgrid["instantiation"].astype(str).eq(TARGET_INSTANTIATION)].copy()

    if acceptance.empty:
        raise ValueError("No fast-pass acceptance rows found for target instantiation")
    if slow_fullgrid.empty:
        raise ValueError("No slow full-grid rows found for target instantiation")

    rows: list[dict] = []

    # Best fast / best nontrivial overall
    best_fast_family = str(merged_summary["best_fast_family"])
    best_fast_config_id = str(merged_summary["best_fast_config_id"])
    fast_row = lookup_config(acceptance, best_fast_family, best_fast_config_id)
    rows.append(
        build_row(
            row_order=1,
            row_label="Nearest nontrivial fast comparator",
            detector_family=best_fast_family,
            config_id=best_fast_config_id,
            fp_cal=fast_row["fp_cal"],
            n_control_alarm_units=fast_row["n_control_alarm_units"],
            n_control_units=fast_row["n_control_units_cal"],
            n_event_alarm_units=fast_row["n_event_alarm_units"],
            n_event_units=fast_row["n_event_units_cal"],
            distance_to_band=fast_row["distance_to_band"],
            interpretation="Nearest nontrivial comparator overall under the locked equal-FP rule.",
        )
    )

    # Numeric nearest slow tied configs
    tied_families = split_semicolon_field(str(merged_summary["numeric_nearest_slow_families_tied"]))
    tied_config_ids = split_semicolon_field(str(merged_summary["numeric_nearest_slow_config_ids_tied"]))
    if len(tied_families) != len(tied_config_ids):
        raise ValueError("numeric_nearest_slow_families_tied and config_ids_tied length mismatch")

    for i, (fam, cfg) in enumerate(zip(tied_families, tied_config_ids), start=1):
        slow_row = lookup_config(slow_fullgrid, fam, cfg)
        rows.append(
            build_row(
                row_order=1 + i,
                row_label=f"Nearest numeric slow tie {i}",
                detector_family=fam,
                config_id=cfg,
                fp_cal=slow_row["fp_cal"],
                n_control_alarm_units=slow_row["n_control_alarm_units"],
                n_control_units=slow_row["n_control_units_cal"],
                n_event_alarm_units=slow_row["n_event_alarm_units"],
                n_event_units=slow_row["n_event_units_cal"],
                distance_to_band=slow_row["distance_to_band"],
                interpretation="Numerically nearest slow config to the band, but trivial-silent.",
            )
        )

    # Best nontrivial slow family
    best_nontrivial_slow_family = str(merged_summary["best_nontrivial_slow_family"])
    best_nontrivial_slow_config_id = str(merged_summary["best_nontrivial_slow_config_id"])
    nontrivial_slow_row = lookup_config(slow_fullgrid, best_nontrivial_slow_family, best_nontrivial_slow_config_id)
    rows.append(
        build_row(
            row_order=10,
            row_label="Best nontrivial slow comparator",
            detector_family=best_nontrivial_slow_family,
            config_id=best_nontrivial_slow_config_id,
            fp_cal=nontrivial_slow_row["fp_cal"],
            n_control_alarm_units=nontrivial_slow_row["n_control_alarm_units"],
            n_control_units=nontrivial_slow_row["n_control_units_cal"],
            n_event_alarm_units=nontrivial_slow_row["n_event_alarm_units"],
            n_event_units=nontrivial_slow_row["n_event_units_cal"],
            distance_to_band=nontrivial_slow_row["distance_to_band"],
            interpretation="Best slow-family config with nonzero event alarms; still materially above band.",
        )
    )

    # Final conclusion row
    rows.append(
        {
            "row_order": 99,
            "row_label": "Final conclusion",
            "detector_family": "—",
            "config_id": "—",
            "fp_cal": pd.NA,
            "control_alarm_units": pd.NA,
            "control_units_total": pd.NA,
            "control_alarm_fraction": "—",
            "event_alarm_units": pd.NA,
            "event_units_total": pd.NA,
            "event_alarm_fraction": "—",
            "distance_to_band": pd.NA,
            "interpretation": (
                "No tested fast or slow comparator configuration achieved the locked equal-FP band; "
                "AC1 remains the nearest nontrivial comparator."
            ),
        }
    )

    out = pd.DataFrame(rows).sort_values("row_order", kind="stable").drop(columns=["row_order"]).reset_index(drop=True)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    OUT_MD.write_text(build_markdown_table(out, freeze_dir), encoding="utf-8")

    print(OUT_CSV)
    print(OUT_MD)
    print()
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
