

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
CONTRACT_FILENAME = f"{BENCHMARK_ID}__contract_freeze.json"
MANIFEST_FILENAME = f"{BENCHMARK_ID}__canonical_user_episode_manifest.csv"
MANIFEST_SUMMARY_FILENAME = f"{BENCHMARK_ID}__canonical_user_episode_manifest_summary.json"
GATE1_JSON_FILENAME = f"{BENCHMARK_ID}__gate1_report.json"
GATE1_MD_FILENAME = f"{BENCHMARK_ID}__gate1_report.md"

EQUAL_FP_LOWER = 0.03
EQUAL_FP_UPPER = 0.07

# Reviewer-conscious minimums for Gate 1.
# These are benchmark-admissibility checks, not significance thresholds.
MIN_MEANINGFUL_EVENT_UNITS = 100
MIN_MEDIAN_WARNING_RUNWAY = 10.0
MIN_MAX_WARNING_RUNWAY = 15


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    results_frozen: Path
    results_manifests: Path
    contract_path: Path
    manifest_path: Path
    manifest_summary_path: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    results_frozen = repo_root / "results" / "frozen"
    results_manifests = repo_root / "results" / "manifests"
    return RepoPaths(
        repo_root=repo_root,
        results_frozen=results_frozen,
        results_manifests=results_manifests,
        contract_path=results_frozen / CONTRACT_FILENAME,
        manifest_path=results_manifests / MANIFEST_FILENAME,
        manifest_summary_path=results_manifests / MANIFEST_SUMMARY_FILENAME,
    )


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_inputs(paths: RepoPaths) -> Tuple[Dict[str, Any], Dict[str, Any], pd.DataFrame]:
    if not paths.contract_path.exists():
        raise FileNotFoundError(
            f"Missing contract freeze: {paths.contract_path}\n"
            f"Run freeze_contract.py first."
        )
    if not paths.manifest_path.exists():
        raise FileNotFoundError(
            f"Missing canonical manifest: {paths.manifest_path}\n"
            f"Run build_user_episode_manifest.py first."
        )
    if not paths.manifest_summary_path.exists():
        raise FileNotFoundError(
            f"Missing manifest summary: {paths.manifest_summary_path}\n"
            f"Run build_user_episode_manifest.py first."
        )

    contract = load_json(paths.contract_path)
    manifest_summary = load_json(paths.manifest_summary_path)
    manifest_df = pd.read_csv(paths.manifest_path)

    if contract.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in contract: {contract.get('benchmark_id')!r}"
        )
    if manifest_summary.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in manifest summary: {manifest_summary.get('benchmark_id')!r}"
        )

    return contract, manifest_summary, manifest_df


def safe_float(x: Any) -> Optional[float]:
    if pd.isna(x):
        return None
    return float(x)


def grid_points_in_band(n_control: int, lower: float, upper: float) -> List[float]:
    if n_control <= 0:
        return []
    pts: List[float] = []
    for k in range(0, n_control + 1):
        fp = k / n_control
        if lower <= fp <= upper:
            pts.append(fp)
    return pts


def summarize_series(values: pd.Series) -> Dict[str, Optional[float]]:
    if len(values) == 0:
        return {"min": None, "p25": None, "median": None, "p75": None, "max": None, "mean": None}
    vals = values.astype(float)
    return {
        "min": float(vals.min()),
        "p25": float(vals.quantile(0.25)),
        "median": float(vals.median()),
        "p75": float(vals.quantile(0.75)),
        "max": float(vals.max()),
        "mean": float(vals.mean()),
    }


def assess_gate1(contract: Dict[str, Any], manifest_summary: Dict[str, Any], manifest_df: pd.DataFrame) -> Dict[str, Any]:
    included = manifest_df[manifest_df["inclusion_status"] == "included"].copy()
    events = included[included["label"] == "event"].copy()
    controls = included[included["label"] == "control"].copy()
    excluded = manifest_df[manifest_df["inclusion_status"] == "excluded"].copy()

    n_total = int(len(manifest_df))
    n_included = int(len(included))
    n_event = int(len(events))
    n_control = int(len(controls))
    n_excluded = int(len(excluded))

    control_grid_step = None if n_control == 0 else 1.0 / n_control
    reachable_points = grid_points_in_band(n_control, EQUAL_FP_LOWER, EQUAL_FP_UPPER)
    equal_fp_band_reachable = len(reachable_points) > 0

    exclusion_counts = (
        excluded["exclusion_reason"].fillna("unknown").value_counts().sort_index().to_dict()
        if n_excluded > 0
        else {}
    )

    event_collapse_summary = summarize_series(events["collapse_step"]) if n_event > 0 else summarize_series(pd.Series(dtype=float))
    event_runway_summary = summarize_series(events["warning_runway_steps"]) if n_event > 0 else summarize_series(pd.Series(dtype=float))
    control_end_summary = summarize_series(controls["episode_end_step"]) if n_control > 0 else summarize_series(pd.Series(dtype=float))

    # Primary admissibility checks
    check_equal_fp_reachable = equal_fp_band_reachable
    check_event_count_meaningful = n_event >= MIN_MEANINGFUL_EVENT_UNITS
    check_runway_median_meaningful = (
        event_runway_summary["median"] is not None and event_runway_summary["median"] >= MIN_MEDIAN_WARNING_RUNWAY
    )
    check_runway_max_meaningful = (
        event_runway_summary["max"] is not None and event_runway_summary["max"] >= MIN_MAX_WARNING_RUNWAY
    )

    hard_failures: List[str] = []
    review_flags: List[str] = []

    if not check_equal_fp_reachable:
        hard_failures.append(
            "equal-FP band [0.03, 0.07] is unreachable on the control-unit grid"
        )

    if n_control <= 0:
        hard_failures.append("no included control units")

    if n_event <= 0:
        hard_failures.append("no included event units")

    if check_equal_fp_reachable and control_grid_step is not None and control_grid_step > (EQUAL_FP_UPPER - EQUAL_FP_LOWER):
        review_flags.append(
            "control FP grid step is coarse relative to the acceptance band width"
        )

    if not check_event_count_meaningful and n_event > 0:
        review_flags.append(
            f"included event count {n_event} is below reviewer-conscious target {MIN_MEANINGFUL_EVENT_UNITS}"
        )

    if not check_runway_median_meaningful and n_event > 0:
        review_flags.append(
            f"median warning runway {event_runway_summary['median']} is below target {MIN_MEDIAN_WARNING_RUNWAY}"
        )

    if not check_runway_max_meaningful and n_event > 0:
        review_flags.append(
            f"max warning runway {event_runway_summary['max']} is below target {MIN_MAX_WARNING_RUNWAY}"
        )

    decision = "PASS"
    if hard_failures:
        decision = "FAIL"
    elif review_flags:
        decision = "REVIEW_REQUIRED"

    if decision == "FAIL":
        recommended_action = (
            "Do not proceed to comparator calibration. Revisit benchmark construction, "
            "unitization, or inclusion criteria before Step 5 benchmark freeze."
        )
    elif decision == "REVIEW_REQUIRED":
        recommended_action = (
            "Benchmark is admissible enough to inspect, but not yet clean enough to treat "
            "as fully reviewer-hardened. Review the flagged conditions before Step 5 benchmark freeze."
        )
    else:
        recommended_action = (
            "Gate 1 passes. You may freeze benchmark state next, then compute Loopzero telemetry "
            "and only after that proceed to comparator calibration."
        )

    report: Dict[str, Any] = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "gate1_check",
        "decision": decision,
        "recommended_action": recommended_action,
        "contract_sha256": contract.get("contract_sha256"),
        "engine_hash": contract.get("engine", {}).get("engine_hash"),
        "equal_fp_contract": {
            "lower": EQUAL_FP_LOWER,
            "upper": EQUAL_FP_UPPER,
        },
        "counts": {
            "n_total_users_processed": n_total,
            "n_included_units": n_included,
            "n_event_units": n_event,
            "n_control_units": n_control,
            "n_excluded_units": n_excluded,
        },
        "control_grid": {
            "grid_step": control_grid_step,
            "reachable_points_in_band": reachable_points,
            "band_reachable": equal_fp_band_reachable,
        },
        "event_collapse_step_summary": event_collapse_summary,
        "event_warning_runway_summary": event_runway_summary,
        "control_episode_end_step_summary": control_end_summary,
        "exclusion_counts": exclusion_counts,
        "checks": {
            "equal_fp_band_reachable": check_equal_fp_reachable,
            "event_count_meaningful": check_event_count_meaningful,
            "event_runway_median_meaningful": check_runway_median_meaningful,
            "event_runway_max_meaningful": check_runway_max_meaningful,
        },
        "review_thresholds": {
            "min_meaningful_event_units": MIN_MEANINGFUL_EVENT_UNITS,
            "min_median_warning_runway": MIN_MEDIAN_WARNING_RUNWAY,
            "min_max_warning_runway": MIN_MAX_WARNING_RUNWAY,
        },
        "hard_failures": hard_failures,
        "review_flags": review_flags,
        "upstream_manifest_summary": manifest_summary,
    }
    return report


def render_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# Gate 1 Report — {report['benchmark_id']}")
    lines.append("")
    lines.append(f"**Decision:** `{report['decision']}`")
    lines.append("")
    lines.append(f"**Recommended action:** {report['recommended_action']}")
    lines.append("")

    counts = report["counts"]
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- total users processed: `{counts['n_total_users_processed']}`")
    lines.append(f"- included units: `{counts['n_included_units']}`")
    lines.append(f"- event units: `{counts['n_event_units']}`")
    lines.append(f"- control units: `{counts['n_control_units']}`")
    lines.append(f"- excluded units: `{counts['n_excluded_units']}`")
    lines.append("")

    grid = report["control_grid"]
    lines.append("## Equal-FP reachability")
    lines.append("")
    lines.append(f"- target band: `[{report['equal_fp_contract']['lower']}, {report['equal_fp_contract']['upper']}]`")
    lines.append(f"- control grid step: `{grid['grid_step']}`")
    lines.append(f"- reachable points in band: `{grid['reachable_points_in_band']}`")
    lines.append(f"- band reachable: `{grid['band_reachable']}`")
    lines.append("")

    def add_summary_block(title: str, block: Dict[str, Any]) -> None:
        lines.append(f"## {title}")
        lines.append("")
        for k in ["min", "p25", "median", "p75", "max", "mean"]:
            lines.append(f"- {k}: `{block.get(k)}`")
        lines.append("")

    add_summary_block("Event collapse-step summary", report["event_collapse_step_summary"])
    add_summary_block("Event warning-runway summary", report["event_warning_runway_summary"])
    add_summary_block("Control episode-end summary", report["control_episode_end_step_summary"])

    lines.append("## Checks")
    lines.append("")
    for name, passed in report["checks"].items():
        icon = "✅" if passed else "⚠️"
        lines.append(f"- {icon} **{name}**: `{passed}`")
    lines.append("")

    lines.append("## Exclusion counts")
    lines.append("")
    if report["exclusion_counts"]:
        for reason, count in report["exclusion_counts"].items():
            lines.append(f"- {reason}: `{count}`")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Hard failures")
    lines.append("")
    if report["hard_failures"]:
        for item in report["hard_failures"]:
            lines.append(f"- ❌ {item}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Review flags")
    lines.append("")
    if report["review_flags"]:
        for item in report["review_flags"]:
            lines.append(f"- ⚠️ {item}")
    else:
        lines.append("- none")
    lines.append("")

    return "\n".join(lines) + "\n"


def write_outputs(paths: RepoPaths, report: Dict[str, Any]) -> Tuple[Path, Path]:
    paths.results_manifests.mkdir(parents=True, exist_ok=True)
    json_path = paths.results_manifests / GATE1_JSON_FILENAME
    md_path = paths.results_manifests / GATE1_MD_FILENAME

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    return json_path, md_path


def run(repo_root: Path) -> Tuple[Path, Path]:
    paths = build_repo_paths(repo_root)
    contract, manifest_summary, manifest_df = ensure_inputs(paths)
    report = assess_gate1(contract, manifest_summary, manifest_df)
    json_path, md_path = write_outputs(paths, report)

    print(f"[ok] wrote Gate 1 JSON: {json_path}")
    print(f"[ok] wrote Gate 1 MD:   {md_path}")
    print(f"[ok] decision:          {report['decision']}")
    print(f"[ok] recommended:       {report['recommended_action']}")
    return json_path, md_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()