

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import pandas as pd


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
CONTRACT_FILENAME = f"{BENCHMARK_ID}__contract_freeze.json"
MANIFEST_FILENAME = f"{BENCHMARK_ID}__canonical_user_episode_manifest.csv"
MANIFEST_SUMMARY_FILENAME = f"{BENCHMARK_ID}__canonical_user_episode_manifest_summary.json"
GATE1_JSON_FILENAME = f"{BENCHMARK_ID}__gate1_report.json"
BENCHMARK_FREEZE_FILENAME = f"{BENCHMARK_ID}__benchmark_freeze_state.json"


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    results_frozen: Path
    results_manifests: Path
    contract_path: Path
    manifest_path: Path
    manifest_summary_path: Path
    gate1_path: Path
    benchmark_freeze_path: Path


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
        gate1_path=results_manifests / GATE1_JSON_FILENAME,
        benchmark_freeze_path=results_frozen / BENCHMARK_FREEZE_FILENAME,
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


def ensure_inputs(paths: RepoPaths) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], pd.DataFrame]:
    missing = [
        str(path)
        for path in [
            paths.contract_path,
            paths.manifest_path,
            paths.manifest_summary_path,
            paths.gate1_path,
        ]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(
            "Missing required benchmark inputs:\n- " + "\n- ".join(missing)
        )

    contract = load_json(paths.contract_path)
    manifest_summary = load_json(paths.manifest_summary_path)
    gate1 = load_json(paths.gate1_path)
    manifest_df = pd.read_csv(paths.manifest_path)

    if contract.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(f"Unexpected benchmark_id in contract: {contract.get('benchmark_id')!r}")
    if manifest_summary.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(f"Unexpected benchmark_id in manifest summary: {manifest_summary.get('benchmark_id')!r}")
    if gate1.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(f"Unexpected benchmark_id in Gate 1 report: {gate1.get('benchmark_id')!r}")

    if gate1.get("decision") != "PASS":
        raise ValueError(
            f"Gate 1 must pass before benchmark freeze. Observed decision: {gate1.get('decision')!r}"
        )

    return contract, manifest_summary, gate1, manifest_df


def build_freeze_payload(
    *,
    paths: RepoPaths,
    contract: Dict[str, Any],
    manifest_summary: Dict[str, Any],
    gate1: Dict[str, Any],
    manifest_df: pd.DataFrame,
) -> Dict[str, Any]:
    included = manifest_df[manifest_df["inclusion_status"] == "included"].copy()
    events = included[included["label"] == "event"].copy()
    controls = included[included["label"] == "control"].copy()

    payload: Dict[str, Any] = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "benchmark_freeze_state",
        "status": "frozen",
        "frozen_inputs": {
            "contract": {
                "path": str(paths.contract_path),
                "sha256": sha256_file(paths.contract_path),
                "contract_sha256": contract.get("contract_sha256"),
            },
            "canonical_manifest": {
                "path": str(paths.manifest_path),
                "sha256": sha256_file(paths.manifest_path),
            },
            "canonical_manifest_summary": {
                "path": str(paths.manifest_summary_path),
                "sha256": sha256_file(paths.manifest_summary_path),
            },
            "gate1_report": {
                "path": str(paths.gate1_path),
                "sha256": sha256_file(paths.gate1_path),
            },
        },
        "frozen_contract": {
            "engine_hash": contract.get("engine", {}).get("engine_hash"),
            "engine_family": contract.get("engine", {}).get("engine_family"),
            "engine_name": contract.get("engine", {}).get("engine_name"),
            "engine_version": contract.get("engine", {}).get("engine_version"),
            "code_commit": contract.get("engine", {}).get("code_commit"),
            "equal_fp_band": {
                "lower": contract.get("comparators", {}).get("equal_fp_band_lower"),
                "upper": contract.get("comparators", {}).get("equal_fp_band_upper"),
            },
            "collapse": contract.get("collapse", {}),
            "robustness": contract.get("robustness", {}),
        },
        "frozen_counts": {
            "n_total_users_processed": int(len(manifest_df)),
            "n_included_units": int(len(included)),
            "n_event_units": int(len(events)),
            "n_control_units": int(len(controls)),
            "n_excluded_units": int(len(manifest_df) - len(included)),
        },
        "frozen_grid": {
            "control_fp_grid_step": gate1.get("control_grid", {}).get("grid_step"),
            "reachable_points_in_band": gate1.get("control_grid", {}).get("reachable_points_in_band"),
            "band_reachable": gate1.get("control_grid", {}).get("band_reachable"),
        },
        "frozen_event_collapse_step_summary": gate1.get("event_collapse_step_summary"),
        "frozen_event_warning_runway_summary": gate1.get("event_warning_runway_summary"),
        "frozen_control_episode_end_step_summary": gate1.get("control_episode_end_step_summary"),
        "frozen_exclusion_counts": gate1.get("exclusion_counts"),
        "gate1_decision": gate1.get("decision"),
        "gate1_recommended_action": gate1.get("recommended_action"),
        "immutability_rule": (
            "After this benchmark freeze, do not alter dataset identity, engine identity, collapse constants, "
            "unitization, inclusion criteria, or canonical benchmark membership before telemetry or comparator calibration."
        ),
        "downstream_rule": (
            "All telemetry, bridge checks, comparator calibration, and manuscript claims for the canonical recommender benchmark "
            "must be derived from this frozen benchmark state."
        ),
        "upstream_manifest_summary": manifest_summary,
    }
    return payload


def write_benchmark_freeze(path: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(payload)
    payload["benchmark_freeze_sha256"] = json_sha256(payload)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def run(repo_root: Path) -> Path:
    paths = build_repo_paths(repo_root)
    contract, manifest_summary, gate1, manifest_df = ensure_inputs(paths)
    payload = build_freeze_payload(
        paths=paths,
        contract=contract,
        manifest_summary=manifest_summary,
        gate1=gate1,
        manifest_df=manifest_df,
    )
    payload = write_benchmark_freeze(paths.benchmark_freeze_path, payload)

    print(f"[ok] wrote benchmark freeze: {paths.benchmark_freeze_path}")
    print(f"[ok] benchmark_id:         {payload['benchmark_id']}")
    print(f"[ok] engine_hash:          {payload['frozen_contract']['engine_hash']}")
    print(f"[ok] freeze_sha256:        {payload['benchmark_freeze_sha256']}")
    return paths.benchmark_freeze_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()