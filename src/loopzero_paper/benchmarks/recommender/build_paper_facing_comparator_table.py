

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
BENCHMARK_FREEZE_FILENAME = f"{BENCHMARK_ID}__benchmark_freeze_state.json"
MERGED_COMPARATOR_SUMMARY_FILENAME = f"{BENCHMARK_ID}__merged_comparator_summary.json"

PAPER_COMPARATOR_TABLE_FILENAME = f"{BENCHMARK_ID}__paper_facing_comparator_table.csv"
PAPER_COMPARATOR_TABLE_MD_FILENAME = f"{BENCHMARK_ID}__paper_facing_comparator_table.md"


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    results_frozen: Path
    results_manifests: Path
    benchmark_freeze_path: Path
    merged_summary_path: Path
    paper_table_path: Path
    paper_table_md_path: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    results_frozen = repo_root / "results" / "frozen"
    results_manifests = repo_root / "results" / "manifests"
    return RepoPaths(
        repo_root=repo_root,
        results_frozen=results_frozen,
        results_manifests=results_manifests,
        benchmark_freeze_path=results_frozen / BENCHMARK_FREEZE_FILENAME,
        merged_summary_path=results_manifests / MERGED_COMPARATOR_SUMMARY_FILENAME,
        paper_table_path=results_manifests / PAPER_COMPARATOR_TABLE_FILENAME,
        paper_table_md_path=results_manifests / PAPER_COMPARATOR_TABLE_MD_FILENAME,
    )


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_inputs(paths: RepoPaths) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    missing = [
        str(path)
        for path in [paths.benchmark_freeze_path, paths.merged_summary_path]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("Missing required paper-table inputs:\n- " + "\n- ".join(missing))

    benchmark_freeze = load_json(paths.benchmark_freeze_path)
    merged_summary = load_json(paths.merged_summary_path)

    if benchmark_freeze.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in benchmark freeze: {benchmark_freeze.get('benchmark_id')!r}"
        )
    if merged_summary.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in merged comparator summary: {merged_summary.get('benchmark_id')!r}"
        )

    if merged_summary.get("benchmark_freeze_sha256") != benchmark_freeze.get("benchmark_freeze_sha256"):
        raise ValueError(
            "Merged comparator summary benchmark_freeze_sha256 does not match the frozen benchmark state."
        )

    return benchmark_freeze, merged_summary


def get_family_block(merged_summary: Dict[str, Any], family: str) -> Dict[str, Any]:
    for group_name in ["fast", "slow"]:
        block = merged_summary.get("groups", {}).get(group_name, {}).get(family)
        if block is not None:
            return {
                "group": group_name,
                **block,
            }
    raise KeyError(f"Missing family in merged comparator summary: {family!r}")


def family_display_name(family: str) -> str:
    mapping = {
        "variance_ews": "Variance EWS",
        "ac1": "AC1",
        "cusum": "CUSUM",
        "page_hinkley": "Page-Hinkley",
        "matrix_profile": "Matrix Profile",
        "permutation_entropy": "Permutation Entropy",
    }
    return mapping.get(family, family)


def fmt_float(x: Any, digits: int = 6) -> str:
    if x is None:
        return "NA"
    return f"{float(x):.{digits}f}"


def build_rows(merged_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    ordered_families = [
        "variance_ews",
        "ac1",
        "cusum",
        "page_hinkley",
        "matrix_profile",
        "permutation_entropy",
    ]

    rows: List[Dict[str, Any]] = []
    for family in ordered_families:
        block = get_family_block(merged_summary, family)
        nearest = block.get("nearest")
        nearest_nontrivial = block.get("nearest_nontrivial")

        row = {
            "family_group": block["group"],
            "family": family,
            "family_display": family_display_name(family),
            "n_configs": int(block.get("n_configs", 0)),
            "n_available_configs": int(block.get("n_available_configs", 0)),
            "n_accepted_configs": int(block.get("n_accepted_configs", 0)),
            "nearest_config_id": None if nearest is None else nearest.get("config_id"),
            "nearest_control_fp": None if nearest is None else nearest.get("control_fp"),
            "nearest_band_distance": None if nearest is None else nearest.get("band_distance"),
            "nearest_event_alarm_rate": None if nearest is None else nearest.get("event_alarm_rate"),
            "nearest_nontrivial_flag": None if nearest is None else nearest.get("nontrivial"),
            "nearest_nontrivial_config_id": None if nearest_nontrivial is None else nearest_nontrivial.get("config_id"),
            "nearest_nontrivial_control_fp": None if nearest_nontrivial is None else nearest_nontrivial.get("control_fp"),
            "nearest_nontrivial_band_distance": None if nearest_nontrivial is None else nearest_nontrivial.get("band_distance"),
            "nearest_nontrivial_event_alarm_rate": None if nearest_nontrivial is None else nearest_nontrivial.get("event_alarm_rate"),
            "accepted_under_equal_fp": bool(int(block.get("n_accepted_configs", 0)) > 0),
        }
        rows.append(row)
    return rows


def build_table_df(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    column_order = [
        "family_group",
        "family_display",
        "n_configs",
        "n_available_configs",
        "n_accepted_configs",
        "accepted_under_equal_fp",
        "nearest_config_id",
        "nearest_control_fp",
        "nearest_band_distance",
        "nearest_event_alarm_rate",
        "nearest_nontrivial_flag",
        "nearest_nontrivial_config_id",
        "nearest_nontrivial_control_fp",
        "nearest_nontrivial_band_distance",
        "nearest_nontrivial_event_alarm_rate",
    ]
    return df[column_order].copy()


def render_markdown_table(benchmark_freeze: Dict[str, Any], merged_summary: Dict[str, Any], df: pd.DataFrame) -> str:
    lower = benchmark_freeze["frozen_contract"]["equal_fp_band"]["lower"]
    upper = benchmark_freeze["frozen_contract"]["equal_fp_band"]["upper"]

    lines: List[str] = []
    lines.append(f"# Paper-Facing Comparator Table — {BENCHMARK_ID}")
    lines.append("")
    lines.append(f"- equal-FP band: `[{lower}, {upper}]`")
    lines.append(f"- total comparator configs: `{merged_summary['totals']['total_configs']}`")
    lines.append(f"- total accepted configs: `{merged_summary['totals']['total_accepted_configs']}`")
    lines.append(f"- no comparator accepted: `{merged_summary['totals']['no_comparator_accepted']}`")
    lines.append("")
    lines.append("| Family | Group | Accepted configs | Nearest FP | Nearest distance | Nearest event rate | Nearest nontrivial FP | Nearest nontrivial distance |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")

    for _, row in df.iterrows():
        lines.append(
            "| "
            f"{row['family_display']} | "
            f"{row['family_group']} | "
            f"{int(row['n_accepted_configs'])} | "
            f"{fmt_float(row['nearest_control_fp'])} | "
            f"{fmt_float(row['nearest_band_distance'])} | "
            f"{fmt_float(row['nearest_event_alarm_rate'])} | "
            f"{fmt_float(row['nearest_nontrivial_control_fp'])} | "
            f"{fmt_float(row['nearest_nontrivial_band_distance'])} |"
        )

    lines.append("")
    lines.append("## Reviewer-facing interpretation")
    lines.append("")
    lines.append("- `Nearest FP` is the numerically nearest operating point to the locked equal-FP band, whether or not it is trivial.")
    lines.append("- `Nearest nontrivial FP` excludes trivial-silent configurations and therefore reflects the closest firing configuration.")
    lines.append("- A family is accepted only if at least one configuration lands inside the prespecified equal-FP band.")
    lines.append("")
    return "\n".join(lines) + "\n"


def write_outputs(paths: RepoPaths, df: pd.DataFrame, md_text: str) -> Tuple[Path, Path]:
    paths.results_manifests.mkdir(parents=True, exist_ok=True)
    df.to_csv(paths.paper_table_path, index=False)
    paths.paper_table_md_path.write_text(md_text, encoding="utf-8")
    return paths.paper_table_path, paths.paper_table_md_path


def run(repo_root: Path) -> Tuple[Path, Path]:
    paths = build_repo_paths(repo_root)
    benchmark_freeze, merged_summary = ensure_inputs(paths)
    rows = build_rows(merged_summary)
    df = build_table_df(rows)
    md_text = render_markdown_table(benchmark_freeze, merged_summary, df)
    csv_path, md_path = write_outputs(paths, df, md_text)

    print(f"[ok] wrote paper-facing comparator table CSV: {csv_path}")
    print(f"[ok] wrote paper-facing comparator table MD:  {md_path}")
    print(f"[ok] no comparator accepted:                {merged_summary['totals']['no_comparator_accepted']}")
    return csv_path, md_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()