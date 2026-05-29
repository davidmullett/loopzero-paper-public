

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
BENCHMARK_FREEZE_FILENAME = f"{BENCHMARK_ID}__benchmark_freeze_state.json"
FAST_MERGED_SUMMARY_FILENAME = f"{BENCHMARK_ID}__fast_merged_summary.json"

GATE2_JSON_FILENAME = f"{BENCHMARK_ID}__gate2_report.json"
GATE2_MD_FILENAME = f"{BENCHMARK_ID}__gate2_report.md"


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    results_frozen: Path
    results_manifests: Path
    benchmark_freeze_path: Path
    fast_merged_summary_path: Path
    gate2_json_path: Path
    gate2_md_path: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    results_frozen = repo_root / "results" / "frozen"
    results_manifests = repo_root / "results" / "manifests"
    return RepoPaths(
        repo_root=repo_root,
        results_frozen=results_frozen,
        results_manifests=results_manifests,
        benchmark_freeze_path=results_frozen / BENCHMARK_FREEZE_FILENAME,
        fast_merged_summary_path=results_manifests / FAST_MERGED_SUMMARY_FILENAME,
        gate2_json_path=results_manifests / GATE2_JSON_FILENAME,
        gate2_md_path=results_manifests / GATE2_MD_FILENAME,
    )


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def json_sha256(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def ensure_inputs(paths: RepoPaths) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    missing = [
        str(path)
        for path in [paths.benchmark_freeze_path, paths.fast_merged_summary_path]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("Missing required Gate 2 inputs:\n- " + "\n- ".join(missing))

    benchmark_freeze = load_json(paths.benchmark_freeze_path)
    fast_summary = load_json(paths.fast_merged_summary_path)

    if benchmark_freeze.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in benchmark freeze: {benchmark_freeze.get('benchmark_id')!r}"
        )
    if fast_summary.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in fast merged summary: {fast_summary.get('benchmark_id')!r}"
        )

    if fast_summary.get("benchmark_freeze_sha256") != benchmark_freeze.get("benchmark_freeze_sha256"):
        raise ValueError(
            "Fast merged summary benchmark_freeze_sha256 does not match the frozen benchmark state."
        )

    return benchmark_freeze, fast_summary


def row_sort_key(row: Dict[str, Any] | None) -> Tuple[Any, ...]:
    if row is None:
        return (1, float("inf"), 0, float("inf"), "")
    available_penalty = 0 if bool(row.get("available")) else 1
    distance = float(row["band_distance"]) if row.get("band_distance") is not None else float("inf")
    nontrivial_bonus = 0 if bool(row.get("nontrivial")) else 1
    event_alarm_penalty = -int(row.get("event_alarm_count", 0))
    config_id = str(row.get("config_id", ""))
    return (available_penalty, distance, nontrivial_bonus, event_alarm_penalty, config_id)


def best_overall(rows: List[Dict[str, Any] | None]) -> Dict[str, Any] | None:
    valid = [row for row in rows if row is not None]
    if not valid:
        return None
    return sorted(valid, key=row_sort_key)[0]


def build_gate2_report(benchmark_freeze: Dict[str, Any], fast_summary: Dict[str, Any]) -> Dict[str, Any]:
    families = fast_summary.get("families", {})

    accepted_families: List[Dict[str, Any]] = []
    nearest_rows: List[Dict[str, Any] | None] = []
    nearest_nontrivial_rows: List[Dict[str, Any] | None] = []

    total_accepted_configs = 0
    total_available_configs = 0
    total_configs = 0

    for family, block in families.items():
        total_configs += int(block.get("n_configs", 0))
        total_available_configs += int(block.get("n_available_configs", 0))
        total_accepted_configs += int(block.get("n_accepted_configs", 0))

        nearest = block.get("nearest")
        nearest_nontrivial = block.get("nearest_nontrivial")
        accepted_best = block.get("accepted_best")

        nearest_rows.append(nearest)
        nearest_nontrivial_rows.append(nearest_nontrivial)

        if int(block.get("n_accepted_configs", 0)) > 0:
            accepted_families.append(
                {
                    "family": family,
                    "n_accepted_configs": int(block.get("n_accepted_configs", 0)),
                    "accepted_best": accepted_best,
                }
            )

    overall_nearest = best_overall(nearest_rows)
    overall_nearest_nontrivial = best_overall(nearest_nontrivial_rows)

    no_fast_family_accepted = total_accepted_configs == 0
    if no_fast_family_accepted:
        decision = "PASS"
        corroboration_survives = True
        recommended_action = (
            "No fast-family comparator achieved an accepted equal-FP operating point. "
            "The recommender branch remains viable as a corroborating flagship benchmark after fast-family testing. "
            "Proceed to slow-family full-grid evaluation."
        )
    else:
        decision = "FAIL"
        corroboration_survives = False
        recommended_action = (
            "At least one fast-family comparator achieved an accepted equal-FP operating point. "
            "Do not continue writing the recommender branch as strong corroboration; move to boundary-case framing."
        )

    report: Dict[str, Any] = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "gate2_check",
        "decision": decision,
        "recommended_action": recommended_action,
        "benchmark_freeze_sha256": benchmark_freeze.get("benchmark_freeze_sha256"),
        "engine_hash": benchmark_freeze.get("frozen_contract", {}).get("engine_hash"),
        "equal_fp_band": benchmark_freeze.get("frozen_contract", {}).get("equal_fp_band"),
        "series_name": fast_summary.get("series_name"),
        "counts": fast_summary.get("counts"),
        "fast_family_summary": {
            "total_configs": total_configs,
            "total_available_configs": total_available_configs,
            "total_accepted_configs": total_accepted_configs,
            "no_fast_family_accepted": no_fast_family_accepted,
            "corroboration_survives_fast_families": corroboration_survives,
        },
        "accepted_families": accepted_families,
        "overall_nearest": overall_nearest,
        "overall_nearest_nontrivial": overall_nearest_nontrivial,
        "families": families,
    }
    return report


def render_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# Gate 2 Report — {report['benchmark_id']}")
    lines.append("")
    lines.append(f"**Decision:** `{report['decision']}`")
    lines.append("")
    lines.append(f"**Recommended action:** {report['recommended_action']}")
    lines.append("")

    lines.append("## Fast-family verdict")
    lines.append("")
    fsum = report["fast_family_summary"]
    lines.append(f"- total_configs: `{fsum['total_configs']}`")
    lines.append(f"- total_available_configs: `{fsum['total_available_configs']}`")
    lines.append(f"- total_accepted_configs: `{fsum['total_accepted_configs']}`")
    lines.append(f"- no_fast_family_accepted: `{fsum['no_fast_family_accepted']}`")
    lines.append(f"- corroboration_survives_fast_families: `{fsum['corroboration_survives_fast_families']}`")
    lines.append("")

    lines.append("## Overall nearest")
    lines.append("")
    overall_nearest = report.get("overall_nearest")
    if overall_nearest is None:
        lines.append("- none")
    else:
        lines.append(f"- family: `{overall_nearest['family']}`")
        lines.append(f"- config_id: `{overall_nearest['config_id']}`")
        lines.append(f"- nontrivial: `{overall_nearest['nontrivial']}`")
        lines.append(f"- control_fp: `{overall_nearest['control_fp']}`")
        lines.append(f"- band_distance: `{overall_nearest['band_distance']}`")
        lines.append(f"- event_alarm_rate: `{overall_nearest['event_alarm_rate']}`")
    lines.append("")

    lines.append("## Overall nearest nontrivial")
    lines.append("")
    overall_nearest_nontrivial = report.get("overall_nearest_nontrivial")
    if overall_nearest_nontrivial is None:
        lines.append("- none")
    else:
        lines.append(f"- family: `{overall_nearest_nontrivial['family']}`")
        lines.append(f"- config_id: `{overall_nearest_nontrivial['config_id']}`")
        lines.append(f"- control_fp: `{overall_nearest_nontrivial['control_fp']}`")
        lines.append(f"- band_distance: `{overall_nearest_nontrivial['band_distance']}`")
        lines.append(f"- event_alarm_rate: `{overall_nearest_nontrivial['event_alarm_rate']}`")
    lines.append("")

    lines.append("## Per-family summary")
    lines.append("")
    for family in ["variance_ews", "ac1", "cusum", "page_hinkley"]:
        block = report["families"].get(family)
        if block is None:
            continue
        lines.append(f"### {family}")
        lines.append("")
        lines.append(f"- n_configs: `{block['n_configs']}`")
        lines.append(f"- n_available_configs: `{block['n_available_configs']}`")
        lines.append(f"- n_accepted_configs: `{block['n_accepted_configs']}`")
        nearest = block.get("nearest")
        nearest_nontrivial = block.get("nearest_nontrivial")
        if nearest is not None:
            lines.append(f"- nearest_config_id: `{nearest['config_id']}`")
            lines.append(f"- nearest_control_fp: `{nearest['control_fp']}`")
            lines.append(f"- nearest_band_distance: `{nearest['band_distance']}`")
            lines.append(f"- nearest_nontrivial_flag: `{nearest['nontrivial']}`")
        if nearest_nontrivial is not None:
            lines.append(f"- nearest_nontrivial_config_id: `{nearest_nontrivial['config_id']}`")
            lines.append(f"- nearest_nontrivial_control_fp: `{nearest_nontrivial['control_fp']}`")
            lines.append(f"- nearest_nontrivial_band_distance: `{nearest_nontrivial['band_distance']}`")
        lines.append("")

    return "\n".join(lines) + "\n"


def write_outputs(paths: RepoPaths, report: Dict[str, Any]) -> Tuple[Path, Path]:
    paths.results_manifests.mkdir(parents=True, exist_ok=True)
    payload = dict(report)
    payload["gate2_report_sha256"] = json_sha256(payload)

    paths.gate2_json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths.gate2_md_path.write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    return paths.gate2_json_path, paths.gate2_md_path


def run(repo_root: Path) -> Tuple[Path, Path]:
    paths = build_repo_paths(repo_root)
    benchmark_freeze, fast_summary = ensure_inputs(paths)
    report = build_gate2_report(benchmark_freeze, fast_summary)
    json_path, md_path = write_outputs(paths, report)

    print(f"[ok] wrote Gate 2 JSON: {json_path}")
    print(f"[ok] wrote Gate 2 MD:   {md_path}")
    print(f"[ok] decision:          {report['decision']}")
    print(f"[ok] recommended:       {report['recommended_action']}")
    return json_path, md_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()