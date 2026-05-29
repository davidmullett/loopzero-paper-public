

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"

BENCHMARK_FREEZE_STATE = f"results/frozen/{BENCHMARK_ID}__benchmark_freeze_state.json"
BRIDGE_CHECK = f"results/manifests/{BENCHMARK_ID}__bridge_check.json"
GATE2_REPORT = f"results/manifests/{BENCHMARK_ID}__gate2_report.json"
MERGED_COMPARATOR_SUMMARY = f"results/manifests/{BENCHMARK_ID}__merged_comparator_summary.json"
PAPER_FACING_COMPARATOR_TABLE = f"results/manifests/{BENCHMARK_ID}__paper_facing_comparator_table.csv"
HORIZON_SENSITIVITY_SUMMARY = f"results/manifests/{BENCHMARK_ID}__horizon_sensitivity_summary.json"
GATE3_REPORT = f"results/manifests/{BENCHMARK_ID}__gate3_report.json"

MANUSCRIPT_FREEZE_STATE_JSON = f"results/frozen/{BENCHMARK_ID}__manuscript_freeze_state.json"
MANUSCRIPT_FREEZE_STATE_MD = f"results/frozen/{BENCHMARK_ID}__manuscript_freeze_state.md"

EXPECTED_FINAL_FRAMING = "corroborating_second_flagship_benchmark_with_bounded_bridge_sensitivity"
EXPECTED_CANONICAL_BRIDGE_DECISION = "PASS"
EXPECTED_H40_BRIDGE_DECISION = "PARTIAL"
EXPECTED_H60_BRIDGE_DECISION = "PASS"
EXPECTED_ACCEPTED_COMPARATORS = 0
EXPECTED_OVERALL_NEAREST_CONFIG_ID = "matrix_profile__44b81bd6"
EXPECTED_CANONICAL_NEAREST_CONTROL_FP = 0.013669821240799159


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    benchmark_freeze_state_path: Path
    bridge_check_path: Path
    gate2_report_path: Path
    merged_comparator_summary_path: Path
    paper_facing_comparator_table_path: Path
    horizon_sensitivity_summary_path: Path
    gate3_report_path: Path
    output_json_path: Path
    output_md_path: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    return RepoPaths(
        repo_root=repo_root,
        benchmark_freeze_state_path=repo_root / BENCHMARK_FREEZE_STATE,
        bridge_check_path=repo_root / BRIDGE_CHECK,
        gate2_report_path=repo_root / GATE2_REPORT,
        merged_comparator_summary_path=repo_root / MERGED_COMPARATOR_SUMMARY,
        paper_facing_comparator_table_path=repo_root / PAPER_FACING_COMPARATOR_TABLE,
        horizon_sensitivity_summary_path=repo_root / HORIZON_SENSITIVITY_SUMMARY,
        gate3_report_path=repo_root / GATE3_REPORT,
        output_json_path=repo_root / MANUSCRIPT_FREEZE_STATE_JSON,
        output_md_path=repo_root / MANUSCRIPT_FREEZE_STATE_MD,
    )


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def json_sha256(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required manuscript-freeze input: {path}")


def ensure_inputs(paths: RepoPaths) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    required_paths = [
        paths.benchmark_freeze_state_path,
        paths.bridge_check_path,
        paths.gate2_report_path,
        paths.merged_comparator_summary_path,
        paths.paper_facing_comparator_table_path,
        paths.horizon_sensitivity_summary_path,
        paths.gate3_report_path,
    ]
    for path in required_paths:
        ensure_exists(path)

    benchmark_freeze = load_json(paths.benchmark_freeze_state_path)
    bridge_check = load_json(paths.bridge_check_path)
    gate2_report = load_json(paths.gate2_report_path)
    merged_comparator_summary = load_json(paths.merged_comparator_summary_path)
    horizon_sensitivity_summary = load_json(paths.horizon_sensitivity_summary_path)
    gate3_report = load_json(paths.gate3_report_path)

    for payload, name in [
        (benchmark_freeze, "benchmark_freeze_state"),
        (bridge_check, "bridge_check"),
        (gate2_report, "gate2_report"),
        (merged_comparator_summary, "merged_comparator_summary"),
        (horizon_sensitivity_summary, "horizon_sensitivity_summary"),
        (gate3_report, "gate3_report"),
    ]:
        if payload.get("benchmark_id") != BENCHMARK_ID:
            raise ValueError(f"Unexpected benchmark_id in {name}: {payload.get('benchmark_id')!r}")

    benchmark_freeze_sha = benchmark_freeze.get("benchmark_freeze_sha256")
    if bridge_check.get("benchmark_freeze_sha256") != benchmark_freeze_sha:
        raise ValueError("bridge_check benchmark_freeze_sha256 does not match benchmark freeze state")
    if gate2_report.get("benchmark_freeze_sha256") != benchmark_freeze_sha:
        raise ValueError("gate2_report benchmark_freeze_sha256 does not match benchmark freeze state")
    if merged_comparator_summary.get("benchmark_freeze_sha256") != benchmark_freeze_sha:
        raise ValueError("merged_comparator_summary benchmark_freeze_sha256 does not match benchmark freeze state")
    if gate3_report.get("benchmark_freeze_sha256") != benchmark_freeze_sha:
        raise ValueError("gate3_report benchmark_freeze_sha256 does not match benchmark freeze state")

    return (
        benchmark_freeze,
        bridge_check,
        gate2_report,
        merged_comparator_summary,
        horizon_sensitivity_summary,
        gate3_report,
    )


def get_horizon(summary: Dict[str, Any], label: str) -> Dict[str, Any]:
    for row in summary.get("horizons", []):
        if row.get("label") == label:
            return row
    raise KeyError(f"Missing horizon label in sensitivity summary: {label!r}")


def assert_expected_facts(
    *,
    merged_comparator_summary: Dict[str, Any],
    horizon_sensitivity_summary: Dict[str, Any],
    gate3_report: Dict[str, Any],
) -> None:
    if gate3_report.get("final_framing") != EXPECTED_FINAL_FRAMING:
        raise ValueError(
            f"Unexpected final framing: {gate3_report.get('final_framing')!r} != {EXPECTED_FINAL_FRAMING!r}"
        )

    canonical = get_horizon(horizon_sensitivity_summary, "canonical_50")
    h40 = get_horizon(horizon_sensitivity_summary, "horizon_40")
    h60 = get_horizon(horizon_sensitivity_summary, "horizon_60")

    if canonical.get("bridge_decision") != EXPECTED_CANONICAL_BRIDGE_DECISION:
        raise ValueError("Canonical bridge decision does not match expected PASS")
    if h40.get("bridge_decision") != EXPECTED_H40_BRIDGE_DECISION:
        raise ValueError("H40 bridge decision does not match expected PARTIAL")
    if h60.get("bridge_decision") != EXPECTED_H60_BRIDGE_DECISION:
        raise ValueError("H60 bridge decision does not match expected PASS")

    if int(canonical.get("accepted_comparator_count")) != EXPECTED_ACCEPTED_COMPARATORS:
        raise ValueError("Canonical accepted comparator count does not match expected 0")
    if int(h40.get("accepted_comparator_count")) != EXPECTED_ACCEPTED_COMPARATORS:
        raise ValueError("H40 accepted comparator count does not match expected 0")
    if int(h60.get("accepted_comparator_count")) != EXPECTED_ACCEPTED_COMPARATORS:
        raise ValueError("H60 accepted comparator count does not match expected 0")

    overall_nearest = merged_comparator_summary.get("overall_nearest")
    if overall_nearest is None:
        raise ValueError("Merged comparator summary missing overall_nearest")

    if overall_nearest.get("config_id") != EXPECTED_OVERALL_NEAREST_CONFIG_ID:
        raise ValueError(
            f"Unexpected overall nearest comparator id: {overall_nearest.get('config_id')!r} != {EXPECTED_OVERALL_NEAREST_CONFIG_ID!r}"
        )

    observed_fp = float(overall_nearest.get("control_fp"))
    if abs(observed_fp - EXPECTED_CANONICAL_NEAREST_CONTROL_FP) > 1e-15:
        raise ValueError(
            f"Unexpected canonical nearest control FP: {observed_fp} != {EXPECTED_CANONICAL_NEAREST_CONTROL_FP}"
        )


def build_payload(
    *,
    paths: RepoPaths,
    benchmark_freeze: Dict[str, Any],
    bridge_check: Dict[str, Any],
    gate2_report: Dict[str, Any],
    merged_comparator_summary: Dict[str, Any],
    horizon_sensitivity_summary: Dict[str, Any],
    gate3_report: Dict[str, Any],
) -> Dict[str, Any]:
    canonical = get_horizon(horizon_sensitivity_summary, "canonical_50")
    h40 = get_horizon(horizon_sensitivity_summary, "horizon_40")
    h60 = get_horizon(horizon_sensitivity_summary, "horizon_60")
    overall_nearest = merged_comparator_summary.get("overall_nearest")

    payload: Dict[str, Any] = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "freeze_manuscript_state",
        "status": "frozen_for_manuscript_drafting",
        "benchmark_freeze_sha": benchmark_freeze.get("benchmark_freeze_sha256"),
        "bridge_check_sha": sha256_file(paths.bridge_check_path),
        "gate2_sha": sha256_file(paths.gate2_report_path),
        "merged_comparator_summary_sha": sha256_file(paths.merged_comparator_summary_path),
        "paper_facing_comparator_table_sha": sha256_file(paths.paper_facing_comparator_table_path),
        "horizon_sensitivity_summary_sha": sha256_file(paths.horizon_sensitivity_summary_path),
        "gate3_sha": sha256_file(paths.gate3_report_path),
        "final_framing": gate3_report.get("final_framing"),
        "canonical_key_facts": {
            "canonical_50": {
                "bridge_decision": canonical.get("bridge_decision"),
                "accepted_comparators": canonical.get("accepted_comparator_count"),
            },
            "horizon_40": {
                "bridge_decision": h40.get("bridge_decision"),
                "accepted_comparators": h40.get("accepted_comparator_count"),
            },
            "horizon_60": {
                "bridge_decision": h60.get("bridge_decision"),
                "accepted_comparators": h60.get("accepted_comparator_count"),
            },
            "overall_nearest_comparator": None if overall_nearest is None else overall_nearest.get("config_id"),
            "nearest_canonical_control_fp": None if overall_nearest is None else overall_nearest.get("control_fp"),
        },
        "authoritative_inputs": {
            "benchmark_freeze_state": {
                "path": str(paths.benchmark_freeze_state_path),
                "sha256": sha256_file(paths.benchmark_freeze_state_path),
            },
            "bridge_check": {
                "path": str(paths.bridge_check_path),
                "sha256": sha256_file(paths.bridge_check_path),
            },
            "gate2_report": {
                "path": str(paths.gate2_report_path),
                "sha256": sha256_file(paths.gate2_report_path),
            },
            "merged_comparator_summary": {
                "path": str(paths.merged_comparator_summary_path),
                "sha256": sha256_file(paths.merged_comparator_summary_path),
            },
            "paper_facing_comparator_table": {
                "path": str(paths.paper_facing_comparator_table_path),
                "sha256": sha256_file(paths.paper_facing_comparator_table_path),
            },
            "horizon_sensitivity_summary": {
                "path": str(paths.horizon_sensitivity_summary_path),
                "sha256": sha256_file(paths.horizon_sensitivity_summary_path),
            },
            "gate3_report": {
                "path": str(paths.gate3_report_path),
                "sha256": sha256_file(paths.gate3_report_path),
            },
        },
        "manuscript_anchor_note": (
            "This artifact freezes the final evidence anchor for manuscript drafting for the canonical recommender branch. "
            "All manuscript claims should trace back to these frozen inputs and the final framing recorded here."
        ),
    }
    return payload


def render_markdown(payload: Dict[str, Any]) -> str:
    kf = payload["canonical_key_facts"]
    lines = [
        f"# Manuscript Freeze State — {payload['benchmark_id']}",
        "",
        f"- status: `{payload['status']}`",
        f"- final_framing: `{payload['final_framing']}`",
        "",
        "## Frozen evidence SHAs",
        "",
        f"- benchmark_freeze_sha: `{payload['benchmark_freeze_sha']}`",
        f"- bridge_check_sha: `{payload['bridge_check_sha']}`",
        f"- gate2_sha: `{payload['gate2_sha']}`",
        f"- merged_comparator_summary_sha: `{payload['merged_comparator_summary_sha']}`",
        f"- paper_facing_comparator_table_sha: `{payload['paper_facing_comparator_table_sha']}`",
        f"- horizon_sensitivity_summary_sha: `{payload['horizon_sensitivity_summary_sha']}`",
        f"- gate3_sha: `{payload['gate3_sha']}`",
        "",
        "## Canonical key facts",
        "",
        f"- 50: bridge `{kf['canonical_50']['bridge_decision']}`, accepted comparators `{kf['canonical_50']['accepted_comparators']}`",
        f"- 40: bridge `{kf['horizon_40']['bridge_decision']}`, accepted comparators `{kf['horizon_40']['accepted_comparators']}`",
        f"- 60: bridge `{kf['horizon_60']['bridge_decision']}`, accepted comparators `{kf['horizon_60']['accepted_comparators']}`",
        f"- overall nearest comparator: `{kf['overall_nearest_comparator']}`",
        f"- nearest canonical control FP: `{kf['nearest_canonical_control_fp']}`",
        "",
        "## Manuscript anchor note",
        "",
        f"- {payload['manuscript_anchor_note']}",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(paths: RepoPaths, payload: Dict[str, Any]) -> Tuple[Path, Path]:
    paths.output_json_path.parent.mkdir(parents=True, exist_ok=True)
    final_payload = dict(payload)
    final_payload["manuscript_freeze_state_sha256"] = json_sha256(final_payload)

    paths.output_json_path.write_text(
        json.dumps(final_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths.output_md_path.write_text(
        render_markdown(final_payload),
        encoding="utf-8",
    )
    return paths.output_json_path, paths.output_md_path


def run(repo_root: Path) -> Tuple[Path, Path]:
    paths = build_repo_paths(repo_root)
    (
        benchmark_freeze,
        bridge_check,
        gate2_report,
        merged_comparator_summary,
        horizon_sensitivity_summary,
        gate3_report,
    ) = ensure_inputs(paths)

    assert_expected_facts(
        merged_comparator_summary=merged_comparator_summary,
        horizon_sensitivity_summary=horizon_sensitivity_summary,
        gate3_report=gate3_report,
    )

    payload = build_payload(
        paths=paths,
        benchmark_freeze=benchmark_freeze,
        bridge_check=bridge_check,
        gate2_report=gate2_report,
        merged_comparator_summary=merged_comparator_summary,
        horizon_sensitivity_summary=horizon_sensitivity_summary,
        gate3_report=gate3_report,
    )
    json_path, md_path = write_outputs(paths, payload)

    print(f"[ok] wrote manuscript freeze JSON: {json_path}")
    print(f"[ok] wrote manuscript freeze MD:   {md_path}")
    print(f"[ok] final framing:                {payload['final_framing']}")
    return json_path, md_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()