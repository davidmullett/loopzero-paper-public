

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
BENCHMARK_FREEZE_FILENAME = f"{BENCHMARK_ID}__benchmark_freeze_state.json"
FAST_MERGED_SUMMARY_FILENAME = f"{BENCHMARK_ID}__fast_merged_summary.json"
SLOW_MERGED_SUMMARY_FILENAME = f"{BENCHMARK_ID}__slow_merged_summary.json"

MERGED_COMPARATOR_SUMMARY_FILENAME = f"{BENCHMARK_ID}__merged_comparator_summary.json"
MERGED_COMPARATOR_SUMMARY_MD_FILENAME = f"{BENCHMARK_ID}__merged_comparator_summary.md"


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    results_frozen: Path
    results_manifests: Path
    benchmark_freeze_path: Path
    fast_summary_path: Path
    slow_summary_path: Path
    merged_summary_path: Path
    merged_summary_md_path: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    results_frozen = repo_root / "results" / "frozen"
    results_manifests = repo_root / "results" / "manifests"
    return RepoPaths(
        repo_root=repo_root,
        results_frozen=results_frozen,
        results_manifests=results_manifests,
        benchmark_freeze_path=results_frozen / BENCHMARK_FREEZE_FILENAME,
        fast_summary_path=results_manifests / FAST_MERGED_SUMMARY_FILENAME,
        slow_summary_path=results_manifests / SLOW_MERGED_SUMMARY_FILENAME,
        merged_summary_path=results_manifests / MERGED_COMPARATOR_SUMMARY_FILENAME,
        merged_summary_md_path=results_manifests / MERGED_COMPARATOR_SUMMARY_MD_FILENAME,
    )


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def json_sha256(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def ensure_inputs(paths: RepoPaths) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    missing = [
        str(path)
        for path in [
            paths.benchmark_freeze_path,
            paths.fast_summary_path,
            paths.slow_summary_path,
        ]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("Missing required comparator-merge inputs:\n- " + "\n- ".join(missing))

    benchmark_freeze = load_json(paths.benchmark_freeze_path)
    fast_summary = load_json(paths.fast_summary_path)
    slow_summary = load_json(paths.slow_summary_path)

    if benchmark_freeze.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in benchmark freeze: {benchmark_freeze.get('benchmark_id')!r}"
        )
    if fast_summary.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in fast merged summary: {fast_summary.get('benchmark_id')!r}"
        )
    if slow_summary.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in slow merged summary: {slow_summary.get('benchmark_id')!r}"
        )

    benchmark_freeze_sha256 = benchmark_freeze.get("benchmark_freeze_sha256")
    if fast_summary.get("benchmark_freeze_sha256") != benchmark_freeze_sha256:
        raise ValueError(
            "Fast merged summary benchmark_freeze_sha256 does not match the frozen benchmark state."
        )
    if slow_summary.get("benchmark_freeze_sha256") != benchmark_freeze_sha256:
        raise ValueError(
            "Slow merged summary benchmark_freeze_sha256 does not match the frozen benchmark state."
        )

    return benchmark_freeze, fast_summary, slow_summary


def row_sort_key(row: Dict[str, Any] | None) -> Tuple[Any, ...]:
    if row is None:
        return (1, float("inf"), 0, float("inf"), "")
    available_penalty = 0 if bool(row.get("available")) else 1
    distance = float(row["band_distance"]) if row.get("band_distance") is not None else float("inf")
    nontrivial_penalty = 0 if bool(row.get("nontrivial")) else 1
    event_alarm_penalty = -int(row.get("event_alarm_count", 0))
    config_id = str(row.get("config_id", ""))
    return (available_penalty, distance, nontrivial_penalty, event_alarm_penalty, config_id)


def best_overall(rows: List[Dict[str, Any] | None]) -> Dict[str, Any] | None:
    valid = [row for row in rows if row is not None]
    if not valid:
        return None
    return sorted(valid, key=row_sort_key)[0]


def flatten_family_rows(summary: Dict[str, Any], group_name: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for family, block in summary.get("families", {}).items():
        row = {
            "group": group_name,
            "family": family,
            "n_configs": int(block.get("n_configs", 0)),
            "n_available_configs": int(block.get("n_available_configs", 0)),
            "n_accepted_configs": int(block.get("n_accepted_configs", 0)),
            "nearest": block.get("nearest"),
            "nearest_nontrivial": block.get("nearest_nontrivial"),
            "accepted_best": block.get("accepted_best"),
        }
        out.append(row)
    return out


def build_merged_summary(
    benchmark_freeze: Dict[str, Any],
    fast_summary: Dict[str, Any],
    slow_summary: Dict[str, Any],
) -> Dict[str, Any]:
    fast_rows = flatten_family_rows(fast_summary, "fast")
    slow_rows = flatten_family_rows(slow_summary, "slow")
    all_rows = fast_rows + slow_rows

    all_nearest = [row.get("nearest") for row in all_rows]
    all_nearest_nontrivial = [row.get("nearest_nontrivial") for row in all_rows]
    all_accepted_best = [row.get("accepted_best") for row in all_rows if row.get("accepted_best") is not None]

    overall_nearest = best_overall(all_nearest)
    overall_nearest_nontrivial = best_overall(all_nearest_nontrivial)
    overall_accepted_best = best_overall(all_accepted_best) if all_accepted_best else None

    total_configs = sum(int(row["n_configs"]) for row in all_rows)
    total_available_configs = sum(int(row["n_available_configs"]) for row in all_rows)
    total_accepted_configs = sum(int(row["n_accepted_configs"]) for row in all_rows)

    report: Dict[str, Any] = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "merge_comparator_summaries",
        "benchmark_freeze_sha256": benchmark_freeze.get("benchmark_freeze_sha256"),
        "engine_hash": benchmark_freeze.get("frozen_contract", {}).get("engine_hash"),
        "series_name": fast_summary.get("series_name"),
        "equal_fp_band": benchmark_freeze.get("frozen_contract", {}).get("equal_fp_band"),
        "counts": benchmark_freeze.get("frozen_counts"),
        "totals": {
            "total_configs": total_configs,
            "total_available_configs": total_available_configs,
            "total_accepted_configs": total_accepted_configs,
            "no_comparator_accepted": total_accepted_configs == 0,
        },
        "overall_nearest": overall_nearest,
        "overall_nearest_nontrivial": overall_nearest_nontrivial,
        "overall_accepted_best": overall_accepted_best,
        "groups": {
            "fast": fast_summary.get("families", {}),
            "slow": slow_summary.get("families", {}),
        },
    }
    return report


def render_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# Merged Comparator Summary — {report['benchmark_id']}")
    lines.append("")
    totals = report["totals"]
    lines.append(f"- total_configs: `{totals['total_configs']}`")
    lines.append(f"- total_available_configs: `{totals['total_available_configs']}`")
    lines.append(f"- total_accepted_configs: `{totals['total_accepted_configs']}`")
    lines.append(f"- no_comparator_accepted: `{totals['no_comparator_accepted']}`")
    lines.append("")

    lines.append("## Overall nearest")
    lines.append("")
    nearest = report.get("overall_nearest")
    if nearest is None:
        lines.append("- none")
    else:
        lines.append(f"- family: `{nearest['family']}`")
        lines.append(f"- config_id: `{nearest['config_id']}`")
        lines.append(f"- nontrivial: `{nearest['nontrivial']}`")
        lines.append(f"- control_fp: `{nearest['control_fp']}`")
        lines.append(f"- band_distance: `{nearest['band_distance']}`")
        lines.append(f"- event_alarm_rate: `{nearest['event_alarm_rate']}`")
    lines.append("")

    lines.append("## Overall nearest nontrivial")
    lines.append("")
    nearest_nontrivial = report.get("overall_nearest_nontrivial")
    if nearest_nontrivial is None:
        lines.append("- none")
    else:
        lines.append(f"- family: `{nearest_nontrivial['family']}`")
        lines.append(f"- config_id: `{nearest_nontrivial['config_id']}`")
        lines.append(f"- control_fp: `{nearest_nontrivial['control_fp']}`")
        lines.append(f"- band_distance: `{nearest_nontrivial['band_distance']}`")
        lines.append(f"- event_alarm_rate: `{nearest_nontrivial['event_alarm_rate']}`")
    lines.append("")

    for group_name in ["fast", "slow"]:
        lines.append(f"## {group_name.capitalize()} families")
        lines.append("")
        families = report["groups"].get(group_name, {})
        for family, block in families.items():
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
    payload["merged_comparator_summary_sha256"] = json_sha256(payload)

    paths.merged_summary_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths.merged_summary_md_path.write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    return paths.merged_summary_path, paths.merged_summary_md_path


def run(repo_root: Path) -> Tuple[Path, Path]:
    paths = build_repo_paths(repo_root)
    benchmark_freeze, fast_summary, slow_summary = ensure_inputs(paths)
    report = build_merged_summary(benchmark_freeze, fast_summary, slow_summary)
    json_path, md_path = write_outputs(paths, report)

    print(f"[ok] wrote merged comparator summary JSON: {json_path}")
    print(f"[ok] wrote merged comparator summary MD:   {md_path}")
    print(f"[ok] total accepted comparators:           {report['totals']['total_accepted_configs']}")
    return json_path, md_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()