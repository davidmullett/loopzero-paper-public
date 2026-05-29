from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
BENCHMARK_FREEZE_FILENAME = f"{BENCHMARK_ID}__benchmark_freeze_state.json"
TELEMETRY_SUMMARY_FILENAME = f"{BENCHMARK_ID}__telemetry_summary.json"

CHECKPOINT_JSON_FILENAME = f"{BENCHMARK_ID}__bridge_checkpoint.json"
CHECKPOINT_MD_FILENAME = f"{BENCHMARK_ID}__bridge_checkpoint.md"


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    results_frozen: Path
    results_manifests: Path
    benchmark_freeze_path: Path
    telemetry_summary_path: Path
    checkpoint_json_path: Path
    checkpoint_md_path: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    results_frozen = repo_root / "results" / "frozen"
    results_manifests = repo_root / "results" / "manifests"
    return RepoPaths(
        repo_root=repo_root,
        results_frozen=results_frozen,
        results_manifests=results_manifests,
        benchmark_freeze_path=results_frozen / BENCHMARK_FREEZE_FILENAME,
        telemetry_summary_path=results_manifests / TELEMETRY_SUMMARY_FILENAME,
        checkpoint_json_path=results_manifests / CHECKPOINT_JSON_FILENAME,
        checkpoint_md_path=results_manifests / CHECKPOINT_MD_FILENAME,
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


def ensure_inputs(paths: RepoPaths) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    missing = [
        str(path)
        for path in [paths.benchmark_freeze_path, paths.telemetry_summary_path]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("Missing required checkpoint inputs:\n- " + "\n- ".join(missing))

    benchmark_freeze = load_json(paths.benchmark_freeze_path)
    telemetry_summary = load_json(paths.telemetry_summary_path)

    if benchmark_freeze.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in benchmark freeze: {benchmark_freeze.get('benchmark_id')!r}"
        )
    if telemetry_summary.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in telemetry summary: {telemetry_summary.get('benchmark_id')!r}"
        )

    if telemetry_summary.get("benchmark_freeze_sha256") != benchmark_freeze.get("benchmark_freeze_sha256"):
        raise ValueError(
            "Telemetry summary benchmark_freeze_sha256 does not match the frozen benchmark state."
        )

    return benchmark_freeze, telemetry_summary


def assess_alignment(telemetry_summary: Dict[str, Any]) -> Dict[str, Any]:
    group_means = telemetry_summary["group_means"]
    event = group_means["precollapse_events"]
    control = group_means["reference_controls"]

    g_event = event["G_mean"]
    g_control = control["G_mean"]

    p_event = event["p_mean"]
    p_control = control["p_mean"]

    d_event = event["delta_mean"]
    d_control = control["delta_mean"]

    g_aligned = (g_event is not None and g_control is not None and g_event > g_control)
    p_aligned = (p_event is not None and p_control is not None and p_event > p_control)
    d_aligned = (d_event is not None and d_control is not None and d_event < d_control)

    aligned_count = sum([g_aligned, p_aligned, d_aligned])

    if aligned_count == 3:
        decision = "PASS"
    elif aligned_count >= 1:
        decision = "PARTIAL"
    else:
        decision = "FAIL"

    return {
        "decision": decision,
        "precollapse_events": {
            "G_mean": g_event,
            "p_mean": p_event,
            "delta_mean": d_event,
        },
        "reference_controls": {
            "G_mean": g_control,
            "p_mean": p_control,
            "delta_mean": d_control,
        },
        "alignment": {
            "G_aligned": g_aligned,
            "p_aligned": p_aligned,
            "delta_aligned": d_aligned,
            "aligned_count": aligned_count,
        },
    }


def build_checkpoint_payload(
    *,
    paths: RepoPaths,
    benchmark_freeze: Dict[str, Any],
    telemetry_summary: Dict[str, Any],
) -> Dict[str, Any]:
    alignment = assess_alignment(telemetry_summary)

    decision = alignment["decision"]
    if decision == "PASS":
        recommended_action = (
            "Bridge appears directionally aligned under the current telemetry package. "
            "Proceed to a formal bridge-check stage and, if confirmed, then to fast-family comparator calibration."
        )
    elif decision == "PARTIAL":
        recommended_action = (
            "Benchmark freeze holds and telemetry completed, but the theorem-to-observable bridge is only partially aligned. "
            "Treat this as an exploratory checkpoint, not manuscript-final, and refine the proxy definitions before comparator calibration."
        )
    else:
        recommended_action = (
            "Benchmark freeze holds and telemetry completed, but the current telemetry package does not support the intended bridge story. "
            "Refine proxy definitions before comparator calibration."
        )

    payload: Dict[str, Any] = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "bridge_checkpoint",
        "checkpoint_status": "telemetry_checkpoint_only",
        "decision": decision,
        "recommended_action": recommended_action,
        "benchmark_freeze_holds": True,
        "telemetry_completed": True,
        "frozen_inputs": {
            "benchmark_freeze": {
                "path": str(paths.benchmark_freeze_path),
                "sha256": sha256_file(paths.benchmark_freeze_path),
                "benchmark_freeze_sha256": benchmark_freeze.get("benchmark_freeze_sha256"),
            },
            "telemetry_summary": {
                "path": str(paths.telemetry_summary_path),
                "sha256": sha256_file(paths.telemetry_summary_path),
            },
        },
        "frozen_contract": {
            "engine_hash": benchmark_freeze["frozen_contract"]["engine_hash"],
            "contract_equal_fp_band": benchmark_freeze["frozen_contract"]["equal_fp_band"],
        },
        "benchmark_counts": benchmark_freeze["frozen_counts"],
        "telemetry_window": {
            "precollapse_window": telemetry_summary.get("precollapse_window"),
        },
        "proxy_alignment": alignment["alignment"],
        "proxy_values": {
            "precollapse_events": alignment["precollapse_events"],
            "reference_controls": alignment["reference_controls"],
        },
        "checkpoint_note": {
            "summary": (
                "Benchmark freeze holds and telemetry completed. "
                "This artifact records an exploratory telemetry checkpoint only."
            ),
            "authority_note": (
                "Formal bridge decisions for robustness and manuscript use must be taken from bridge_check.py, "
                "not this checkpoint artifact."
            ),
            "manuscript_status": (
                "Do not treat this telemetry checkpoint as a manuscript-final bridge decision."
            ),
        },
        "next_steps": [
            "Use bridge_check.py as the formal bridge decision artifact.",
            "Use gate2_check.py for fast-family adjudication.",
            "Use merged comparator summaries and the paper-facing table for comparator claims.",
            "Treat this checkpoint as descriptive telemetry provenance only.",
        ],
    }

    return payload


def render_markdown(payload: Dict[str, Any]) -> str:
    a = payload["proxy_alignment"]
    pv = payload["proxy_values"]

    lines = []
    lines.append(f"# Bridge Checkpoint — {payload['benchmark_id']}")
    lines.append("")
    lines.append(f"**Status:** `{payload['checkpoint_status']}`")
    lines.append("")
    lines.append(f"**Decision:** `{payload['decision']}`")
    lines.append("")
    lines.append(f"**Recommended action:** {payload['recommended_action']}")
    lines.append("")
    lines.append("## Checkpoint note")
    lines.append("")
    lines.append(f"- benchmark freeze holds: `{payload['benchmark_freeze_holds']}`")
    lines.append(f"- telemetry completed: `{payload['telemetry_completed']}`")
    lines.append(f"- G aligned: `{a['G_aligned']}`")
    lines.append(f"- p aligned: `{a['p_aligned']}`")
    lines.append(f"- delta aligned: `{a['delta_aligned']}`")
    lines.append("")
    lines.append("## Proxy values")
    lines.append("")
    lines.append("### Pre-collapse events")
    lines.append("")
    lines.append(f"- G_mean: `{pv['precollapse_events']['G_mean']}`")
    lines.append(f"- p_mean: `{pv['precollapse_events']['p_mean']}`")
    lines.append(f"- delta_mean: `{pv['precollapse_events']['delta_mean']}`")
    lines.append("")
    lines.append("### Reference controls")
    lines.append("")
    lines.append(f"- G_mean: `{pv['reference_controls']['G_mean']}`")
    lines.append(f"- p_mean: `{pv['reference_controls']['p_mean']}`")
    lines.append(f"- delta_mean: `{pv['reference_controls']['delta_mean']}`")
    lines.append("")
    lines.append("## Summary note")
    lines.append("")
    lines.append(f"- {payload['checkpoint_note']['summary']}")
    lines.append(f"- {payload['checkpoint_note']['authority_note']}")
    lines.append(f"- {payload['checkpoint_note']['manuscript_status']}")
    lines.append("")
    lines.append("## Next steps")
    lines.append("")
    for step in payload["next_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def write_outputs(paths: RepoPaths, payload: Dict[str, Any]) -> Tuple[Path, Path]:
    paths.results_manifests.mkdir(parents=True, exist_ok=True)

    payload = dict(payload)
    payload["bridge_checkpoint_sha256"] = json_sha256(payload)

    paths.checkpoint_json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths.checkpoint_md_path.write_text(
        render_markdown(payload) + "\n",
        encoding="utf-8",
    )

    return paths.checkpoint_json_path, paths.checkpoint_md_path


def run(repo_root: Path) -> Tuple[Path, Path]:
    paths = build_repo_paths(repo_root)
    benchmark_freeze, telemetry_summary = ensure_inputs(paths)
    payload = build_checkpoint_payload(
        paths=paths,
        benchmark_freeze=benchmark_freeze,
        telemetry_summary=telemetry_summary,
    )
    json_path, md_path = write_outputs(paths, payload)

    print(f"[ok] wrote bridge checkpoint JSON: {json_path}")
    print(f"[ok] wrote bridge checkpoint MD:   {md_path}")
    print(f"[ok] decision:                     {payload['decision']}")
    print(f"[ok] note:                         {payload['checkpoint_note']['summary']}")
    return json_path, md_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()