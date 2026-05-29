

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
BENCHMARK_FREEZE_FILENAME = f"{BENCHMARK_ID}__benchmark_freeze_state.json"
TELEMETRY_PANEL_FILENAME = f"{BENCHMARK_ID}__telemetry_panel.csv.gz"
TELEMETRY_SUMMARY_FILENAME = f"{BENCHMARK_ID}__telemetry_summary.json"

BRIDGE_CHECK_JSON_FILENAME = f"{BENCHMARK_ID}__bridge_check.json"
BRIDGE_CHECK_MD_FILENAME = f"{BENCHMARK_ID}__bridge_check.md"

BOOTSTRAP_SEED = 0
BOOTSTRAP_REPS = 1000


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    results_frozen: Path
    results_manifests: Path
    benchmark_freeze_path: Path
    telemetry_panel_path: Path
    telemetry_summary_path: Path
    bridge_check_json_path: Path
    bridge_check_md_path: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    results_frozen = repo_root / "results" / "frozen"
    results_manifests = repo_root / "results" / "manifests"
    return RepoPaths(
        repo_root=repo_root,
        results_frozen=results_frozen,
        results_manifests=results_manifests,
        benchmark_freeze_path=results_frozen / BENCHMARK_FREEZE_FILENAME,
        telemetry_panel_path=results_manifests / TELEMETRY_PANEL_FILENAME,
        telemetry_summary_path=results_manifests / TELEMETRY_SUMMARY_FILENAME,
        bridge_check_json_path=results_manifests / BRIDGE_CHECK_JSON_FILENAME,
        bridge_check_md_path=results_manifests / BRIDGE_CHECK_MD_FILENAME,
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


def ensure_inputs(paths: RepoPaths) -> Tuple[Dict[str, Any], Dict[str, Any], pd.DataFrame]:
    missing = [
        str(path)
        for path in [
            paths.benchmark_freeze_path,
            paths.telemetry_panel_path,
            paths.telemetry_summary_path,
        ]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("Missing required bridge-check inputs:\n- " + "\n- ".join(missing))

    benchmark_freeze = load_json(paths.benchmark_freeze_path)
    telemetry_summary = load_json(paths.telemetry_summary_path)
    telemetry_panel = pd.read_csv(paths.telemetry_panel_path, compression="gzip")

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

    return benchmark_freeze, telemetry_summary, telemetry_panel


def bootstrap_mean_ci(values: np.ndarray, *, reps: int = BOOTSTRAP_REPS, seed: int = BOOTSTRAP_SEED) -> Dict[str, float | int | None]:
    arr = np.asarray(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    n = len(arr)
    if n == 0:
        return {
            "n_users": 0,
            "mean": None,
            "ci_lower": None,
            "ci_upper": None,
        }

    rng = np.random.default_rng(seed)
    means = np.empty(reps, dtype=float)
    for i in range(reps):
        sample = arr[rng.integers(0, n, size=n)]
        means[i] = float(sample.mean())

    return {
        "n_users": int(n),
        "mean": float(arr.mean()),
        "ci_lower": float(np.percentile(means, 2.5)),
        "ci_upper": float(np.percentile(means, 97.5)),
    }


def per_user_metric_means(df: pd.DataFrame, metric: str) -> np.ndarray:
    grouped = df.groupby("user_id", sort=False)[metric].mean()
    return grouped.to_numpy(dtype=float)


def assess_bridge(benchmark_freeze: Dict[str, Any], telemetry_summary: Dict[str, Any], telemetry_panel: pd.DataFrame) -> Dict[str, Any]:
    precollapse_window = int(telemetry_summary["precollapse_window"])

    event_df = telemetry_panel[
        (telemetry_panel["label"] == "event")
        & (telemetry_panel["is_precollapse_window"] == True)
    ].copy()

    control_df = telemetry_panel[
        (telemetry_panel["label"] == "control")
        & (telemetry_panel["step"] > (telemetry_panel["natural_alarm_window_end_step"] - precollapse_window))
    ].copy()

    metrics = ["G", "p", "delta"]
    metric_results: Dict[str, Any] = {}
    aligned_count = 0

    metric_seeds = {"G": BOOTSTRAP_SEED + 11, "p": BOOTSTRAP_SEED + 22, "delta": BOOTSTRAP_SEED + 33}

    for metric in metrics:
        event_stats = bootstrap_mean_ci(per_user_metric_means(event_df, metric), seed=metric_seeds[metric])
        control_stats = bootstrap_mean_ci(per_user_metric_means(control_df, metric), seed=metric_seeds[metric] + 1000)

        event_mean = event_stats["mean"]
        control_mean = control_stats["mean"]

        if metric in {"G", "p"}:
            aligned = bool(event_mean is not None and control_mean is not None and event_mean > control_mean)
        else:
            aligned = bool(event_mean is not None and control_mean is not None and event_mean < control_mean)

        aligned_count += int(aligned)
        metric_results[metric] = {
            "precollapse_events": event_stats,
            "reference_controls": control_stats,
            "aligned": aligned,
            "difference_event_minus_control": None if event_mean is None or control_mean is None else float(event_mean - control_mean),
            "expected_direction": "event>control" if metric in {"G", "p"} else "event<control",
        }

    if aligned_count == 3:
        decision = "PASS"
    elif aligned_count >= 1:
        decision = "PARTIAL"
    else:
        decision = "FAIL"

    if decision == "PASS":
        recommended_action = (
            "Bridge check passes under the current telemetry package. Proceed to fast-family comparator calibration."
        )
    elif decision == "PARTIAL":
        recommended_action = (
            "Bridge check is only partially aligned. Refine telemetry proxies before comparator calibration."
        )
    else:
        recommended_action = (
            "Bridge check fails. Do not proceed to comparator calibration until telemetry semantics are revised."
        )

    report: Dict[str, Any] = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "bridge_check",
        "decision": decision,
        "recommended_action": recommended_action,
        "benchmark_freeze_sha256": benchmark_freeze.get("benchmark_freeze_sha256"),
        "engine_hash": benchmark_freeze.get("frozen_contract", {}).get("engine_hash"),
        "precollapse_window": precollapse_window,
        "bootstrap": {
            "seed": BOOTSTRAP_SEED,
            "reps": BOOTSTRAP_REPS,
            "unit": "user",
            "note": "User-level bootstrap is descriptive uncertainty only; bridge decision is directional, not a significance test.",
        },
        "counts": {
            "n_unique_users_in_panel": int(telemetry_panel["user_id"].nunique()),
            "n_event_rows_in_bridge_window": int(len(event_df)),
            "n_control_rows_in_bridge_window": int(len(control_df)),
            "n_event_users_in_bridge_window": int(event_df["user_id"].nunique()),
            "n_control_users_in_bridge_window": int(control_df["user_id"].nunique()),
        },
        "metrics": metric_results,
        "aligned_count": aligned_count,
        "all_aligned": aligned_count == 3,
    }
    return report


def render_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# Bridge Check — {report['benchmark_id']}")
    lines.append("")
    lines.append(f"**Decision:** `{report['decision']}`")
    lines.append("")
    lines.append(f"**Recommended action:** {report['recommended_action']}")
    lines.append("")
    lines.append("## Bootstrap")
    lines.append("")
    lines.append(f"- unit: `{report['bootstrap']['unit']}`")
    lines.append(f"- reps: `{report['bootstrap']['reps']}`")
    lines.append(f"- seed: `{report['bootstrap']['seed']}`")
    lines.append(f"- note: {report['bootstrap']['note']}")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    for k, v in report["counts"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Metric checks")
    lines.append("")
    for metric in ["G", "p", "delta"]:
        block = report["metrics"][metric]
        event_stats = block["precollapse_events"]
        control_stats = block["reference_controls"]
        lines.append(f"### {metric}")
        lines.append("")
        lines.append(f"- aligned: `{block['aligned']}`")
        lines.append(f"- expected_direction: `{block['expected_direction']}`")
        lines.append(f"- event_mean: `{event_stats['mean']}`")
        lines.append(f"- event_ci: `[{event_stats['ci_lower']}, {event_stats['ci_upper']}]`")
        lines.append(f"- control_mean: `{control_stats['mean']}`")
        lines.append(f"- control_ci: `[{control_stats['ci_lower']}, {control_stats['ci_upper']}]`")
        lines.append(f"- difference_event_minus_control: `{block['difference_event_minus_control']}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_outputs(paths: RepoPaths, report: Dict[str, Any]) -> Tuple[Path, Path]:
    paths.results_manifests.mkdir(parents=True, exist_ok=True)
    payload = dict(report)
    payload["bridge_check_sha256"] = json_sha256(payload)

    paths.bridge_check_json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths.bridge_check_md_path.write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    return paths.bridge_check_json_path, paths.bridge_check_md_path


def run(repo_root: Path) -> Tuple[Path, Path]:
    paths = build_repo_paths(repo_root)
    benchmark_freeze, telemetry_summary, telemetry_panel = ensure_inputs(paths)
    report = assess_bridge(benchmark_freeze, telemetry_summary, telemetry_panel)
    json_path, md_path = write_outputs(paths, report)

    print(f"[ok] wrote bridge-check JSON: {json_path}")
    print(f"[ok] wrote bridge-check MD:   {md_path}")
    print(f"[ok] decision:                {report['decision']}")
    print(f"[ok] recommended:             {report['recommended_action']}")
    return json_path, md_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()