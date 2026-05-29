

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
HORIZON_SENSITIVITY_SUMMARY = f"results/manifests/{BENCHMARK_ID}__horizon_sensitivity_summary.json"
MERGED_COMPARATOR_SUMMARY = f"results/manifests/{BENCHMARK_ID}__merged_comparator_summary.json"
BENCHMARK_FREEZE_STATE = f"results/frozen/{BENCHMARK_ID}__benchmark_freeze_state.json"

GATE3_REPORT_JSON = f"results/manifests/{BENCHMARK_ID}__gate3_report.json"
GATE3_REPORT_MD = f"results/manifests/{BENCHMARK_ID}__gate3_report.md"


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    horizon_sensitivity_path: Path
    merged_comparator_path: Path
    benchmark_freeze_path: Path
    output_json_path: Path
    output_md_path: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    return RepoPaths(
        repo_root=repo_root,
        horizon_sensitivity_path=repo_root / HORIZON_SENSITIVITY_SUMMARY,
        merged_comparator_path=repo_root / MERGED_COMPARATOR_SUMMARY,
        benchmark_freeze_path=repo_root / BENCHMARK_FREEZE_STATE,
        output_json_path=repo_root / GATE3_REPORT_JSON,
        output_md_path=repo_root / GATE3_REPORT_MD,
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


def get_horizon(summary: Dict[str, Any], label: str) -> Dict[str, Any]:
    for horizon in summary.get("horizons", []):
        if horizon.get("label") == label:
            return horizon
    raise KeyError(f"Missing horizon label: {label!r}")


def build_gate3_report(
    benchmark_freeze: Dict[str, Any],
    horizon_summary: Dict[str, Any],
    merged_comparator: Dict[str, Any],
) -> Dict[str, Any]:
    canonical = get_horizon(horizon_summary, "canonical_50")
    h40 = get_horizon(horizon_summary, "horizon_40")
    h60 = get_horizon(horizon_summary, "horizon_60")

    canonical_bridge_pass = canonical.get("bridge_decision") == "PASS"
    h40_bridge_pass = h40.get("bridge_decision") == "PASS"
    h60_bridge_pass = h60.get("bridge_decision") == "PASS"

    canonical_no_accept = bool(canonical.get("no_comparator_accepted"))
    h40_no_accept = bool(h40.get("no_comparator_accepted"))
    h60_no_accept = bool(h60.get("no_comparator_accepted"))

    all_horizons_no_accept = canonical_no_accept and h40_no_accept and h60_no_accept
    all_horizons_bridge_pass = canonical_bridge_pass and h40_bridge_pass and h60_bridge_pass
    bounded_bridge_sensitivity = canonical_bridge_pass and h60_bridge_pass and not h40_bridge_pass

    if all_horizons_no_accept and all_horizons_bridge_pass:
        final_framing = "corroborating_second_flagship_benchmark"
        decision = "PASS"
        recommended_action = (
            "The recommender branch supports a corroborating second flagship benchmark under canonical and adjacent-horizon robustness. "
            "Proceed to manuscript freeze with standard robustness language."
        )
    elif all_horizons_no_accept and bounded_bridge_sensitivity:
        final_framing = "corroborating_second_flagship_benchmark_with_bounded_bridge_sensitivity"
        decision = "PASS_WITH_QUALIFICATION"
        recommended_action = (
            "The recommender branch supports a corroborating second flagship benchmark on the comparator claim, "
            "with a bounded robustness qualification on the theorem-to-observable bridge under adjacent horizon shortening. "
            "Proceed to manuscript freeze using qualified robustness language."
        )
    elif not all_horizons_no_accept:
        final_framing = "bounded_residual"
        decision = "FAIL_CORROBORATION"
        recommended_action = (
            "At least one horizon admits accepted comparator configurations. Do not frame the recommender branch as strong corroboration; "
            "rewrite it as a bounded residual or boundary-case branch."
        )
    else:
        final_framing = "falsification_branch"
        decision = "FAIL_BRIDGE"
        recommended_action = (
            "Comparator robustness holds, but bridge instability is too severe for flagship corroboration. "
            "Use falsification-boundary framing instead of strong corroboration language."
        )

    report = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "gate3_check",
        "decision": decision,
        "final_framing": final_framing,
        "recommended_action": recommended_action,
        "benchmark_freeze_sha256": benchmark_freeze.get("benchmark_freeze_sha256"),
        "engine_hash": benchmark_freeze.get("frozen_contract", {}).get("engine_hash"),
        "canonical_horizon": benchmark_freeze.get("frozen_contract", {}).get("robustness", {}).get("canonical_horizon"),
        "horizon_summary": {
            "canonical_50": canonical,
            "horizon_40": h40,
            "horizon_60": h60,
        },
        "adjudication": {
            "all_horizons_no_accept": all_horizons_no_accept,
            "all_horizons_bridge_pass": all_horizons_bridge_pass,
            "bounded_bridge_sensitivity": bounded_bridge_sensitivity,
            "canonical_bridge_pass": canonical_bridge_pass,
            "h40_bridge_pass": h40_bridge_pass,
            "h60_bridge_pass": h60_bridge_pass,
        },
        "canonical_comparator_context": {
            "overall_nearest": merged_comparator.get("overall_nearest"),
            "overall_nearest_nontrivial": merged_comparator.get("overall_nearest_nontrivial"),
            "total_accepted_configs": merged_comparator.get("totals", {}).get("total_accepted_configs"),
        },
    }
    return report


def render_row(horizon: Dict[str, Any]) -> List[str]:
    lines = [
        f"- bridge_decision: `{horizon['bridge_decision']}`",
        f"- bridge_aligned_count: `{horizon['bridge_aligned_count']}`",
        f"- accepted_comparator_count: `{horizon['accepted_comparator_count']}`",
        f"- no_comparator_accepted: `{horizon['no_comparator_accepted']}`",
    ]
    nearest = horizon.get("overall_nearest")
    if nearest is not None:
        lines.extend([
            f"- nearest_family: `{nearest['family']}`",
            f"- nearest_config_id: `{nearest['config_id']}`",
            f"- nearest_control_fp: `{nearest['control_fp']}`",
            f"- nearest_band_distance: `{nearest['band_distance']}`",
        ])
    return lines


def render_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# Gate 3 Report — {report['benchmark_id']}")
    lines.append("")
    lines.append(f"**Decision:** `{report['decision']}`")
    lines.append("")
    lines.append(f"**Final framing:** `{report['final_framing']}`")
    lines.append("")
    lines.append(f"**Recommended action:** {report['recommended_action']}")
    lines.append("")

    lines.append("## Adjudication")
    lines.append("")
    adj = report["adjudication"]
    lines.append(f"- all_horizons_no_accept: `{adj['all_horizons_no_accept']}`")
    lines.append(f"- all_horizons_bridge_pass: `{adj['all_horizons_bridge_pass']}`")
    lines.append(f"- bounded_bridge_sensitivity: `{adj['bounded_bridge_sensitivity']}`")
    lines.append(f"- canonical_bridge_pass: `{adj['canonical_bridge_pass']}`")
    lines.append(f"- h40_bridge_pass: `{adj['h40_bridge_pass']}`")
    lines.append(f"- h60_bridge_pass: `{adj['h60_bridge_pass']}`")
    lines.append("")

    lines.append("## Horizon-by-horizon summary")
    lines.append("")
    for label in ["canonical_50", "horizon_40", "horizon_60"]:
        horizon = report["horizon_summary"][label]
        lines.append(f"### {label}")
        lines.append("")
        lines.extend(render_row(horizon))
        lines.append("")

    lines.append("## Canonical comparator context")
    lines.append("")
    context = report["canonical_comparator_context"]
    lines.append(f"- total_accepted_configs: `{context['total_accepted_configs']}`")
    nearest = context.get("overall_nearest")
    if nearest is not None:
        lines.append(f"- overall_nearest_family: `{nearest['family']}`")
        lines.append(f"- overall_nearest_config_id: `{nearest['config_id']}`")
        lines.append(f"- overall_nearest_control_fp: `{nearest['control_fp']}`")
        lines.append(f"- overall_nearest_band_distance: `{nearest['band_distance']}`")
    nearest_nontrivial = context.get("overall_nearest_nontrivial")
    if nearest_nontrivial is not None:
        lines.append(f"- overall_nearest_nontrivial_family: `{nearest_nontrivial['family']}`")
        lines.append(f"- overall_nearest_nontrivial_config_id: `{nearest_nontrivial['config_id']}`")
        lines.append(f"- overall_nearest_nontrivial_control_fp: `{nearest_nontrivial['control_fp']}`")
        lines.append(f"- overall_nearest_nontrivial_band_distance: `{nearest_nontrivial['band_distance']}`")
    lines.append("")
    return "\n".join(lines) + "\n"


def write_outputs(paths: RepoPaths, report: Dict[str, Any]) -> Tuple[Path, Path]:
    paths.output_json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(report)
    payload["gate3_report_sha256"] = json_sha256(payload)

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
    ensure_exists(paths.horizon_sensitivity_path)
    ensure_exists(paths.merged_comparator_path)
    ensure_exists(paths.benchmark_freeze_path)

    horizon_summary = load_json(paths.horizon_sensitivity_path)
    merged_comparator = load_json(paths.merged_comparator_path)
    benchmark_freeze = load_json(paths.benchmark_freeze_path)

    report = build_gate3_report(benchmark_freeze, horizon_summary, merged_comparator)
    json_path, md_path = write_outputs(paths, report)

    print(f"[ok] wrote Gate 3 JSON: {json_path}")
    print(f"[ok] wrote Gate 3 MD:   {md_path}")
    print(f"[ok] decision:          {report['decision']}")
    print(f"[ok] final framing:     {report['final_framing']}")
    return json_path, md_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()