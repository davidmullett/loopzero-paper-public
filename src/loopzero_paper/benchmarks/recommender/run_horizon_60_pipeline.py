from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
TARGET_HORIZON = 60
PACKET_NAME = f"{BENCHMARK_ID}__horizon_60_packet"

RESULT_FILES: List[str] = [
    "results/frozen/movielens25m_recursive_frontier_public_v1__contract_freeze.json",
    "results/frozen/movielens25m_recursive_frontier_public_v1__benchmark_freeze_state.json",
    "results/manifests/movielens25m_recursive_frontier_public_v1__canonical_user_episode_manifest.csv",
    "results/manifests/movielens25m_recursive_frontier_public_v1__canonical_user_episode_manifest_summary.json",
    "results/manifests/movielens25m_recursive_frontier_public_v1__gate1_report.json",
    "results/manifests/movielens25m_recursive_frontier_public_v1__gate1_report.md",
    "results/manifests/movielens25m_recursive_frontier_public_v1__telemetry_panel.csv.gz",
    "results/manifests/movielens25m_recursive_frontier_public_v1__telemetry_summary.json",
    "results/manifests/movielens25m_recursive_frontier_public_v1__bridge_checkpoint.json",
    "results/manifests/movielens25m_recursive_frontier_public_v1__bridge_checkpoint.md",
    "results/manifests/movielens25m_recursive_frontier_public_v1__bridge_check.json",
    "results/manifests/movielens25m_recursive_frontier_public_v1__bridge_check.md",
    "results/manifests/movielens25m_recursive_frontier_public_v1__fast_availability_table.csv",
    "results/manifests/movielens25m_recursive_frontier_public_v1__fast_calibration_matrix.csv",
    "results/manifests/movielens25m_recursive_frontier_public_v1__fast_merged_summary.json",
    "results/manifests/movielens25m_recursive_frontier_public_v1__gate2_report.json",
    "results/manifests/movielens25m_recursive_frontier_public_v1__gate2_report.md",
    "results/manifests/movielens25m_recursive_frontier_public_v1__slow_availability_table.csv",
    "results/manifests/movielens25m_recursive_frontier_public_v1__slow_calibration_matrix.csv",
    "results/manifests/movielens25m_recursive_frontier_public_v1__slow_merged_summary.json",
    "results/manifests/movielens25m_recursive_frontier_public_v1__merged_comparator_summary.json",
    "results/manifests/movielens25m_recursive_frontier_public_v1__merged_comparator_summary.md",
    "results/manifests/movielens25m_recursive_frontier_public_v1__paper_facing_comparator_table.csv",
    "results/manifests/movielens25m_recursive_frontier_public_v1__paper_facing_comparator_table.md",
]

PIPELINE_SCRIPTS: List[str] = [
    "src/loopzero_paper/benchmarks/recommender/build_user_episode_manifest.py",
    "src/loopzero_paper/benchmarks/recommender/gate1_check.py",
    "src/loopzero_paper/benchmarks/recommender/freeze_benchmark_state.py",
    "src/loopzero_paper/benchmarks/recommender/compute_telemetry.py",
    "src/loopzero_paper/benchmarks/recommender/freeze_bridge_checkpoint.py",
    "src/loopzero_paper/benchmarks/recommender/bridge_check.py",
    "src/loopzero_paper/benchmarks/recommender/calibrate_fast_families.py",
    "src/loopzero_paper/benchmarks/recommender/gate2_check.py",
    "src/loopzero_paper/benchmarks/recommender/calibrate_slow_families.py",
    "src/loopzero_paper/benchmarks/recommender/merge_comparator_summaries.py",
    "src/loopzero_paper/benchmarks/recommender/build_paper_facing_comparator_table.py",
]


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    contract_path: Path
    backup_dir: Path
    packet_dir: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    return RepoPaths(
        repo_root=repo_root,
        contract_path=repo_root / "results" / "frozen" / f"{BENCHMARK_ID}__contract_freeze.json",
        backup_dir=repo_root / "results" / "robustness" / "recommender" / "_tmp_restore_h60",
        packet_dir=repo_root / "results" / "robustness" / "recommender" / PACKET_NAME,
    )


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def snapshot_existing_outputs(paths: RepoPaths) -> None:
    if paths.backup_dir.exists():
        shutil.rmtree(paths.backup_dir)
    paths.backup_dir.mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, bool] = {}
    for rel in RESULT_FILES:
        src = paths.repo_root / rel
        manifest[rel] = src.exists()
        if src.exists():
            dst = paths.backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    write_json(paths.backup_dir / "backup_manifest.json", manifest)


def restore_outputs(paths: RepoPaths) -> None:
    manifest_path = paths.backup_dir / "backup_manifest.json"
    if not manifest_path.exists():
        return

    manifest = load_json(manifest_path)
    for rel, existed in manifest.items():
        dst = paths.repo_root / rel
        backup_src = paths.backup_dir / rel
        if existed:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_src, dst)
        else:
            if dst.exists():
                dst.unlink()


def override_contract_horizon(paths: RepoPaths) -> None:
    payload = load_json(paths.contract_path)
    payload["collapse"]["max_horizon_steps"] = TARGET_HORIZON
    if "robustness" in payload:
        payload["robustness"]["canonical_horizon"] = TARGET_HORIZON
    payload["horizon_sensitivity_override"] = {
        "target_horizon": TARGET_HORIZON,
        "note": "Temporary contract override used only to generate adjacent-horizon robustness packet.",
    }
    write_json(paths.contract_path, payload)


def run_pipeline_scripts(paths: RepoPaths) -> None:
    for rel in PIPELINE_SCRIPTS:
        script_path = paths.repo_root / rel
        print(f"[h60] running {rel}")
        subprocess.run([sys.executable, str(script_path)], cwd=str(paths.repo_root), check=True)


def archive_packet(paths: RepoPaths) -> None:
    if paths.packet_dir.exists():
        shutil.rmtree(paths.packet_dir)
    paths.packet_dir.mkdir(parents=True, exist_ok=True)

    archived_files: List[str] = []
    for rel in RESULT_FILES:
        src = paths.repo_root / rel
        if src.exists():
            dst = paths.packet_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            archived_files.append(rel)

    metadata = {
        "benchmark_id": BENCHMARK_ID,
        "target_horizon": TARGET_HORIZON,
        "packet_name": PACKET_NAME,
        "packet_dir": str(paths.packet_dir),
        "archived_files": archived_files,
        "note": (
            "This packet was generated by temporarily overriding max_horizon_steps to 60, rerunning the full recommender pipeline, "
            "archiving the resulting artifacts, and then restoring the canonical horizon-50 outputs."
        ),
    }
    write_json(paths.packet_dir / "packet_metadata.json", metadata)


def run(repo_root: Path) -> Path:
    paths = build_repo_paths(repo_root)
    if not paths.contract_path.exists():
        raise FileNotFoundError(f"Missing canonical contract freeze: {paths.contract_path}")

    snapshot_existing_outputs(paths)
    try:
        override_contract_horizon(paths)
        run_pipeline_scripts(paths)
        archive_packet(paths)
    finally:
        restore_outputs(paths)

    print(f"[ok] archived horizon-60 packet: {paths.packet_dir}")
    return paths.packet_dir


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()
