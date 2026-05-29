

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"

CANONICAL_BRIDGE_CHECK = f"results/manifests/{BENCHMARK_ID}__bridge_check.json"
CANONICAL_MERGED_COMPARATOR = f"results/manifests/{BENCHMARK_ID}__merged_comparator_summary.json"
CANONICAL_BENCHMARK_FREEZE = f"results/frozen/{BENCHMARK_ID}__benchmark_freeze_state.json"

H40_PACKET_DIR = f"results/robustness/recommender/{BENCHMARK_ID}__horizon_40_packet"
H60_PACKET_DIR = f"results/robustness/recommender/{BENCHMARK_ID}__horizon_60_packet"

HORIZON_SENSITIVITY_SUMMARY_JSON = f"results/manifests/{BENCHMARK_ID}__horizon_sensitivity_summary.json"
HORIZON_SENSITIVITY_SUMMARY_MD = f"results/manifests/{BENCHMARK_ID}__horizon_sensitivity_summary.md"


@dataclass(frozen=True)
class HorizonSource:
    label: str
    horizon: int
    benchmark_freeze_path: Path
    bridge_check_path: Path
    merged_comparator_path: Path


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    canonical_source: HorizonSource
    h40_source: HorizonSource
    h60_source: HorizonSource
    output_json_path: Path
    output_md_path: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    canonical_source = HorizonSource(
        label="canonical_50",
        horizon=50,
        benchmark_freeze_path=repo_root / CANONICAL_BENCHMARK_FREEZE,
        bridge_check_path=repo_root / CANONICAL_BRIDGE_CHECK,
        merged_comparator_path=repo_root / CANONICAL_MERGED_COMPARATOR,
    )
    h40_source = HorizonSource(
        label="horizon_40",
        horizon=40,
        benchmark_freeze_path=repo_root / H40_PACKET_DIR / "results/frozen" / f"{BENCHMARK_ID}__benchmark_freeze_state.json",
        bridge_check_path=repo_root / H40_PACKET_DIR / "results/manifests" / f"{BENCHMARK_ID}__bridge_check.json",
        merged_comparator_path=repo_root / H40_PACKET_DIR / "results/manifests" / f"{BENCHMARK_ID}__merged_comparator_summary.json",
    )
    h60_source = HorizonSource(
        label="horizon_60",
        horizon=60,
        benchmark_freeze_path=repo_root / H60_PACKET_DIR / "results/frozen" / f"{BENCHMARK_ID}__benchmark_freeze_state.json",
        bridge_check_path=repo_root / H60_PACKET_DIR / "results/manifests" / f"{BENCHMARK_ID}__bridge_check.json",
        merged_comparator_path=repo_root / H60_PACKET_DIR / "results/manifests" / f"{BENCHMARK_ID}__merged_comparator_summary.json",
    )
    return RepoPaths(
        repo_root=repo_root,
        canonical_source=canonical_source,
        h40_source=h40_source,
        h60_source=h60_source,
        output_json_path=repo_root / HORIZON_SENSITIVITY_SUMMARY_JSON,
        output_md_path=repo_root / HORIZON_SENSITIVITY_SUMMARY_MD,
    )


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def json_sha256(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")


def extract_overall_nearest(merged: Dict[str, Any]) -> Dict[str, Any] | None:
    row = merged.get("overall_nearest")
    if row is None:
        return None
    return {
        "family": row.get("family"),
        "config_id": row.get("config_id"),
        "nontrivial": row.get("nontrivial"),
        "control_fp": row.get("control_fp"),
        "band_distance": row.get("band_distance"),
        "event_alarm_rate": row.get("event_alarm_rate"),
    }


def extract_overall_nearest_nontrivial(merged: Dict[str, Any]) -> Dict[str, Any] | None:
    row = merged.get("overall_nearest_nontrivial")
    if row is None:
        return None
    return {
        "family": row.get("family"),
        "config_id": row.get("config_id"),
        "control_fp": row.get("control_fp"),
        "band_distance": row.get("band_distance"),
        "event_alarm_rate": row.get("event_alarm_rate"),
    }


def summarize_horizon(source: HorizonSource) -> Dict[str, Any]:
    ensure_exists(source.benchmark_freeze_path)
    ensure_exists(source.bridge_check_path)
    ensure_exists(source.merged_comparator_path)

    benchmark_freeze = load_json(source.benchmark_freeze_path)
    bridge_check = load_json(source.bridge_check_path)
    merged = load_json(source.merged_comparator_path)

    summary = {
        "label": source.label,
        "horizon": source.horizon,
        "benchmark_freeze_sha256": benchmark_freeze.get("benchmark_freeze_sha256"),
        "bridge_decision": bridge_check.get("decision"),
        "bridge_recommended_action": bridge_check.get("recommended_action"),
        "bridge_aligned_count": bridge_check.get("aligned_count"),
        "bridge_all_aligned": bridge_check.get("all_aligned"),
        "accepted_comparator_count": merged.get("totals", {}).get("total_accepted_configs"),
        "no_comparator_accepted": merged.get("totals", {}).get("no_comparator_accepted"),
        "overall_nearest": extract_overall_nearest(merged),
        "overall_nearest_nontrivial": extract_overall_nearest_nontrivial(merged),
    }
    return summary


def build_report(paths: RepoPaths) -> Dict[str, Any]:
    horizons = [
        summarize_horizon(paths.canonical_source),
        summarize_horizon(paths.h40_source),
        summarize_horizon(paths.h60_source),
    ]

    report = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "merge_horizon_sensitivity_results",
        "horizons": horizons,
        "summary": {
            "canonical_bridge_decision": horizons[0]["bridge_decision"],
            "h40_bridge_decision": horizons[1]["bridge_decision"],
            "h60_bridge_decision": horizons[2]["bridge_decision"],
            "canonical_accepted_comparators": horizons[0]["accepted_comparator_count"],
            "h40_accepted_comparators": horizons[1]["accepted_comparator_count"],
            "h60_accepted_comparators": horizons[2]["accepted_comparator_count"],
        },
    }
    return report


def render_row(row: Dict[str, Any] | None, *, include_nontrivial_flag: bool) -> List[str]:
    if row is None:
        return [
            "- family: `none`",
            "- config_id: `none`",
            "- control_fp: `NA`",
            "- band_distance: `NA`",
            "- event_alarm_rate: `NA`",
        ]
    lines = [
        f"- family: `{row['family']}`",
        f"- config_id: `{row['config_id']}`",
        f"- control_fp: `{row['control_fp']}`",
        f"- band_distance: `{row['band_distance']}`",
        f"- event_alarm_rate: `{row['event_alarm_rate']}`",
    ]
    if include_nontrivial_flag:
        lines.insert(2, f"- nontrivial: `{row['nontrivial']}`")
    return lines


def render_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# Horizon Sensitivity Summary — {report['benchmark_id']}")
    lines.append("")

    for horizon in report["horizons"]:
        lines.append(f"## {horizon['label']} (horizon={horizon['horizon']})")
        lines.append("")
        lines.append(f"- bridge_decision: `{horizon['bridge_decision']}`")
        lines.append(f"- bridge_aligned_count: `{horizon['bridge_aligned_count']}`")
        lines.append(f"- bridge_all_aligned: `{horizon['bridge_all_aligned']}`")
        lines.append(f"- accepted_comparator_count: `{horizon['accepted_comparator_count']}`")
        lines.append(f"- no_comparator_accepted: `{horizon['no_comparator_accepted']}`")
        lines.append("")
        lines.append("### Overall nearest")
        lines.append("")
        lines.extend(render_row(horizon["overall_nearest"], include_nontrivial_flag=True))
        lines.append("")
        lines.append("### Overall nearest nontrivial")
        lines.append("")
        lines.extend(render_row(horizon["overall_nearest_nontrivial"], include_nontrivial_flag=False))
        lines.append("")

    lines.append("## Cross-horizon view")
    lines.append("")
    summary = report["summary"]
    lines.append(f"- canonical_bridge_decision: `{summary['canonical_bridge_decision']}`")
    lines.append(f"- h40_bridge_decision: `{summary['h40_bridge_decision']}`")
    lines.append(f"- h60_bridge_decision: `{summary['h60_bridge_decision']}`")
    lines.append(f"- canonical_accepted_comparators: `{summary['canonical_accepted_comparators']}`")
    lines.append(f"- h40_accepted_comparators: `{summary['h40_accepted_comparators']}`")
    lines.append(f"- h60_accepted_comparators: `{summary['h60_accepted_comparators']}`")
    lines.append("")
    return "\n".join(lines) + "\n"


def write_outputs(paths: RepoPaths, report: Dict[str, Any]) -> Tuple[Path, Path]:
    paths.output_json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(report)
    payload["horizon_sensitivity_summary_sha256"] = json_sha256(payload)

    paths.output_json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths.output_md_path.write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    return paths.output_json_path, paths.output_md_path


def run(repo_root: Path) -> Tuple[Path, Path]:
    paths = build_repo_paths(repo_root)
    report = build_report(paths)
    json_path, md_path = write_outputs(paths, report)

    print(f"[ok] wrote horizon sensitivity summary JSON: {json_path}")
    print(f"[ok] wrote horizon sensitivity summary MD:   {md_path}")
    return json_path, md_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()