from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"

FIGURE_TABLE_MAP_JSON = f"results/manifests/{BENCHMARK_ID}__figure_table_map.json"
FIGURE_TABLE_MAP_MD = f"results/manifests/{BENCHMARK_ID}__figure_table_map.md"

MARKETS_EQUAL_FP_TABLE = "results/frozen/table2_equal_fp.csv"
MARKETS_DOMAIN_TABLE = "results/frozen/table1_domains.csv"

RECOMMENDER_BRIDGE_CHECK = f"results/manifests/{BENCHMARK_ID}__bridge_check.json"
RECOMMENDER_MERGED_COMPARATOR = f"results/manifests/{BENCHMARK_ID}__merged_comparator_summary.json"
RECOMMENDER_HORIZON_SENSITIVITY = f"results/manifests/{BENCHMARK_ID}__horizon_sensitivity_summary.json"
RECOMMENDER_PAPER_TABLE = f"results/manifests/{BENCHMARK_ID}__paper_facing_comparator_table.csv"
MANUSCRIPT_FREEZE_STATE = f"results/frozen/{BENCHMARK_ID}__manuscript_freeze_state.json"


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    output_json_path: Path
    output_md_path: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    return RepoPaths(
        repo_root=repo_root,
        output_json_path=repo_root / FIGURE_TABLE_MAP_JSON,
        output_md_path=repo_root / FIGURE_TABLE_MAP_MD,
    )


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


def describe_artifact(repo_root: Path, rel_path: str) -> Dict[str, Any]:
    path = repo_root / rel_path
    return {
        "path": rel_path,
        "exists": path.exists(),
        "sha256": sha256_file(path) if path.exists() else None,
    }


def build_map(repo_root: Path) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = [
        {
            "order": 1,
            "type": "figure",
            "id": "Fig. 1",
            "title": "Canonical markets comparator calibration under locked equal-FP",
            "purpose": (
                "Show the canonical markets branch as a benchmark-level comparator result, "
                "with the accepted band visible and nearest/nearest-nontrivial families legible."
            ),
            "input_artifacts": [
                describe_artifact(repo_root, MARKETS_EQUAL_FP_TABLE),
                describe_artifact(repo_root, MARKETS_DOMAIN_TABLE),
            ],
            "planned_outputs": [
                "results/figures/fig1_markets_canonical_comparator_band.png",
                "results/figures/fig1_markets_canonical_comparator_band.pdf",
                "results/source_data/fig1_markets_canonical_comparator_band.csv",
            ],
            "manuscript_role": "main_text",
        },
        {
            "order": 2,
            "type": "figure",
            "id": "Fig. 2",
            "title": "Canonical recommender bridge and comparator result",
            "purpose": (
                "Show the canonical 50-step recommender bridge on G, p, and delta, together with "
                "family-level comparator failure under the same locked equal-FP contract."
            ),
            "input_artifacts": [
                describe_artifact(repo_root, RECOMMENDER_BRIDGE_CHECK),
                describe_artifact(repo_root, RECOMMENDER_MERGED_COMPARATOR),
            ],
            "planned_outputs": [
                "results/figures/fig2_recommender_canonical_bridge_and_comparators.png",
                "results/figures/fig2_recommender_canonical_bridge_and_comparators.pdf",
                "results/source_data/fig2_recommender_bridge.csv",
                "results/source_data/fig2_recommender_comparators.csv",
            ],
            "manuscript_role": "main_text",
        },
        {
            "order": 3,
            "type": "figure",
            "id": "Fig. 3",
            "title": "Adjacent-horizon sensitivity in the recommender benchmark",
            "purpose": (
                "Show bridge decision by horizon and nearest comparator behavior by horizon, "
                "making the bounded bridge qualification immediately legible."
            ),
            "input_artifacts": [
                describe_artifact(repo_root, RECOMMENDER_HORIZON_SENSITIVITY),
            ],
            "planned_outputs": [
                "results/figures/fig3_recommender_horizon_sensitivity.png",
                "results/figures/fig3_recommender_horizon_sensitivity.pdf",
                "results/source_data/fig3_recommender_horizon_sensitivity.csv",
            ],
            "manuscript_role": "main_text",
        },
        {
            "order": 4,
            "type": "table",
            "id": "Table 1",
            "title": "Main-text comparator calibration table",
            "purpose": (
                "Provide the compact, reviewer-facing cross-family comparator table used in the main text."
            ),
            "input_artifacts": [
                describe_artifact(repo_root, RECOMMENDER_PAPER_TABLE),
                describe_artifact(repo_root, MANUSCRIPT_FREEZE_STATE),
            ],
            "planned_outputs": [
                "results/tables/table1_main_text_comparator_table.csv",
                "results/tables/table1_main_text_comparator_table.md",
                "results/source_data/table1_main_text_comparator_table.csv",
            ],
            "manuscript_role": "main_text",
        },
        {
            "order": 5,
            "type": "table_bundle",
            "id": "Supplementary Tables",
            "title": "Supplementary comparator and robustness tables",
            "purpose": (
                "Export supplementary markets, recommender, and horizon-sensitivity tables once the main figures and table are frozen."
            ),
            "input_artifacts": [
                describe_artifact(repo_root, RECOMMENDER_MERGED_COMPARATOR),
                describe_artifact(repo_root, RECOMMENDER_HORIZON_SENSITIVITY),
            ],
            "planned_outputs": [
                "results/tables/tableSx_markets_comparator_detail.csv",
                "results/tables/tableSy_recommender_comparator_detail.csv",
                "results/tables/tableSz_recommender_horizon_sensitivity.csv",
            ],
            "manuscript_role": "supplement",
        },
        {
            "order": 6,
            "type": "source_data_bundle",
            "id": "Source Data",
            "title": "Source-data exports for all main figures and tables",
            "purpose": (
                "Provide explicit source-data files for all main-text figures and tables."
            ),
            "input_artifacts": [
                describe_artifact(repo_root, MARKETS_EQUAL_FP_TABLE),
                describe_artifact(repo_root, RECOMMENDER_BRIDGE_CHECK),
                describe_artifact(repo_root, RECOMMENDER_MERGED_COMPARATOR),
                describe_artifact(repo_root, RECOMMENDER_HORIZON_SENSITIVITY),
                describe_artifact(repo_root, RECOMMENDER_PAPER_TABLE),
            ],
            "planned_outputs": [
                "results/source_data/fig1_markets_canonical_comparator_band.csv",
                "results/source_data/fig2_recommender_bridge.csv",
                "results/source_data/fig2_recommender_comparators.csv",
                "results/source_data/fig3_recommender_horizon_sensitivity.csv",
                "results/source_data/table1_main_text_comparator_table.csv",
            ],
            "manuscript_role": "supporting",
        },
    ]

    payload = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "build_figure_table_map",
        "entries": entries,
    }
    return payload


def render_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# Figure/Table Map — {payload['benchmark_id']}")
    lines.append("")
    for entry in payload["entries"]:
        lines.append(f"## {entry['id']} — {entry['title']}")
        lines.append("")
        lines.append(f"- order: `{entry['order']}`")
        lines.append(f"- type: `{entry['type']}`")
        lines.append(f"- manuscript_role: `{entry['manuscript_role']}`")
        lines.append(f"- purpose: {entry['purpose']}")
        lines.append("")
        lines.append("### Input artifacts")
        lines.append("")
        for art in entry["input_artifacts"]:
            lines.append(f"- `{art['path']}` — exists: `{art['exists']}`")
        lines.append("")
        lines.append("### Planned outputs")
        lines.append("")
        for out in entry["planned_outputs"]:
            lines.append(f"- `{out}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_outputs(paths: RepoPaths, payload: Dict[str, Any]) -> Tuple[Path, Path]:
    paths.output_json_path.parent.mkdir(parents=True, exist_ok=True)
    final_payload = dict(payload)
    final_payload["figure_table_map_sha256"] = json_sha256(final_payload)

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
    payload = build_map(repo_root)
    return write_outputs(paths, payload)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    json_path, md_path = run(repo_root)
    print(f"[ok] wrote figure/table map JSON: {json_path}")
    print(f"[ok] wrote figure/table map MD:   {md_path}")


if __name__ == "__main__":
    main()