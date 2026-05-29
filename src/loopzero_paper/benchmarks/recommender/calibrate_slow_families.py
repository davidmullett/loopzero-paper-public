

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
BENCHMARK_FREEZE_FILENAME = f"{BENCHMARK_ID}__benchmark_freeze_state.json"
TELEMETRY_PANEL_FILENAME = f"{BENCHMARK_ID}__telemetry_panel.csv.gz"

SLOW_AVAILABILITY_TABLE_FILENAME = f"{BENCHMARK_ID}__slow_availability_table.csv"
SLOW_CALIBRATION_MATRIX_FILENAME = f"{BENCHMARK_ID}__slow_calibration_matrix.csv"
SLOW_MERGED_SUMMARY_FILENAME = f"{BENCHMARK_ID}__slow_merged_summary.json"

SERIES_NAME = "miss_run_fraction"
EPS = 1e-12


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    results_frozen: Path
    results_manifests: Path
    benchmark_freeze_path: Path
    telemetry_panel_path: Path
    slow_availability_table_path: Path
    slow_calibration_matrix_path: Path
    slow_merged_summary_path: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    results_frozen = repo_root / "results" / "frozen"
    results_manifests = repo_root / "results" / "manifests"
    return RepoPaths(
        repo_root=repo_root,
        results_frozen=results_frozen,
        results_manifests=results_manifests,
        benchmark_freeze_path=results_frozen / BENCHMARK_FREEZE_FILENAME,
        telemetry_panel_path=results_manifests / TELEMETRY_PANEL_FILENAME,
        slow_availability_table_path=results_manifests / SLOW_AVAILABILITY_TABLE_FILENAME,
        slow_calibration_matrix_path=results_manifests / SLOW_CALIBRATION_MATRIX_FILENAME,
        slow_merged_summary_path=results_manifests / SLOW_MERGED_SUMMARY_FILENAME,
    )


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def json_sha256(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def stable_config_id(family: str, params: Dict[str, Any]) -> str:
    blob = json.dumps({"family": family, "params": params}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"{family}__{hashlib.sha256(blob.encode('utf-8')).hexdigest()[:8]}"


def ensure_inputs(paths: RepoPaths) -> Tuple[Dict[str, Any], pd.DataFrame]:
    missing = [
        str(path)
        for path in [paths.benchmark_freeze_path, paths.telemetry_panel_path]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("Missing required slow-family inputs:\n- " + "\n- ".join(missing))

    benchmark_freeze = load_json(paths.benchmark_freeze_path)
    telemetry_panel = pd.read_csv(
        paths.telemetry_panel_path,
        compression="gzip",
        usecols=[
            "user_id",
            "label",
            "step",
            "natural_alarm_window_start_step",
            "natural_alarm_window_end_step",
            "consecutive_misses_after_step",
            "benchmark_freeze_sha256",
        ],
    )

    if benchmark_freeze.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in benchmark freeze: {benchmark_freeze.get('benchmark_id')!r}"
        )

    observed_freeze_shas = sorted(set(str(x) for x in telemetry_panel["benchmark_freeze_sha256"].dropna().unique().tolist()))
    if observed_freeze_shas != [benchmark_freeze.get("benchmark_freeze_sha256")]:
        raise ValueError(
            "Telemetry panel benchmark_freeze_sha256 does not match the frozen benchmark state."
        )

    return benchmark_freeze, telemetry_panel


def build_user_series(
    benchmark_freeze: Dict[str, Any],
    telemetry_panel: pd.DataFrame,
) -> Tuple[Dict[int, np.ndarray], Dict[int, str], Dict[str, int], int]:
    collapse_streak_len = int(benchmark_freeze["frozen_contract"]["collapse"]["collapse_streak_len"])

    df = telemetry_panel.copy()
    df = df[
        (df["step"] >= df["natural_alarm_window_start_step"])
        & (df["step"] <= df["natural_alarm_window_end_step"])
    ].copy()
    df["x"] = np.minimum(1.0, df["consecutive_misses_after_step"].astype(float) / collapse_streak_len)
    df = df.sort_values(["user_id", "step"], kind="mergesort")

    series_by_user: Dict[int, np.ndarray] = {}
    label_by_user: Dict[int, str] = {}

    for user_id, g in df.groupby("user_id", sort=False):
        uid = int(user_id)
        label = str(g["label"].iloc[0])
        series_by_user[uid] = g["x"].to_numpy(dtype=float, copy=True)
        label_by_user[uid] = label

    counts = {
        "n_users": len(series_by_user),
        "n_event_users": sum(1 for label in label_by_user.values() if label == "event"),
        "n_control_users": sum(1 for label in label_by_user.values() if label == "control"),
    }
    min_series_len = min(len(x) for x in series_by_user.values()) if series_by_user else 0
    return series_by_user, label_by_user, counts, min_series_len


def z_norm(x: np.ndarray) -> np.ndarray:
    mean = float(x.mean())
    std = float(x.std())
    if std <= EPS:
        return np.zeros_like(x, dtype=float)
    return (x - mean) / std


def matrix_profile_score(series: np.ndarray, window: int) -> float:
    n = len(series)
    if n < window + 1:
        return float("nan")

    windows = np.lib.stride_tricks.sliding_window_view(np.asarray(series, dtype=float), window_shape=window)
    m = windows.shape[0]
    if m < 2:
        return float("nan")

    subseqs = np.vstack([z_norm(w) for w in windows])
    profile = np.full(m, np.inf, dtype=float)

    for i in range(m):
        for j in range(i + 1, m):
            dist = float(np.linalg.norm(subseqs[i] - subseqs[j])) / math.sqrt(window)
            if dist < profile[i]:
                profile[i] = dist
            if dist < profile[j]:
                profile[j] = dist

    finite = profile[np.isfinite(profile)]
    if len(finite) == 0:
        return float("nan")
    return float(finite.max())


def ordinal_pattern(window: np.ndarray, order: int) -> Tuple[int, ...]:
    idx = np.argsort(np.asarray(window, dtype=float), kind="mergesort")
    return tuple(int(i) for i in idx[:order])


def permutation_entropy_score(series: np.ndarray, order: int, delay: int) -> float:
    x = np.asarray(series, dtype=float)
    needed = (order - 1) * delay + 1
    if len(x) < needed + 1:
        return float("nan")

    patterns: Dict[Tuple[int, ...], int] = {}
    total = 0
    for start in range(0, len(x) - (order - 1) * delay):
        idx = start + np.arange(order) * delay
        pattern = ordinal_pattern(x[idx], order=order)
        patterns[pattern] = patterns.get(pattern, 0) + 1
        total += 1

    if total == 0:
        return float("nan")

    probs = np.array([count / total for count in patterns.values()], dtype=float)
    entropy = float(-(probs * np.log(probs + EPS)).sum())
    max_entropy = math.log(math.factorial(order))
    if max_entropy <= EPS:
        return float("nan")
    return float(entropy / max_entropy)


def matrix_profile_alarm(series: np.ndarray, *, window: int, threshold: float) -> bool:
    score = matrix_profile_score(series, window)
    if np.isnan(score):
        return False
    return bool(score >= threshold)


def permutation_entropy_alarm(series: np.ndarray, *, order: int, delay: int, threshold: float) -> bool:
    score = permutation_entropy_score(series, order, delay)
    if np.isnan(score):
        return False
    # Low entropy = more regular / collapsed dynamics
    return bool(score <= threshold)


def slow_family_grids() -> Dict[str, List[Dict[str, Any]]]:
    return {
        "matrix_profile": [
            {"window": w, "threshold": th}
            for w, th in itertools.product([4, 5, 6, 7, 8], [0.20, 0.30, 0.40, 0.50, 0.60])
        ],
        "permutation_entropy": [
            {"order": order, "delay": delay, "threshold": th}
            for order, delay, th in itertools.product([3, 4], [1, 2], [0.20, 0.35, 0.50, 0.65, 0.80])
        ],
    }


def required_min_len(family: str, params: Dict[str, Any]) -> int:
    if family == "matrix_profile":
        return int(params["window"]) + 1
    if family == "permutation_entropy":
        return (int(params["order"]) - 1) * int(params["delay"]) + 2
    raise ValueError(f"Unknown family: {family!r}")


def family_alarm(series: np.ndarray, family: str, params: Dict[str, Any]) -> bool:
    if family == "matrix_profile":
        return matrix_profile_alarm(series, window=int(params["window"]), threshold=float(params["threshold"]))
    if family == "permutation_entropy":
        return permutation_entropy_alarm(
            series,
            order=int(params["order"]),
            delay=int(params["delay"]),
            threshold=float(params["threshold"]),
        )
    raise ValueError(f"Unknown family: {family!r}")


def band_distance(fp: float, lower: float, upper: float) -> float:
    if lower <= fp <= upper:
        return 0.0
    if fp < lower:
        return lower - fp
    return fp - upper


def evaluate_config(
    *,
    family: str,
    params: Dict[str, Any],
    series_by_user: Dict[int, np.ndarray],
    label_by_user: Dict[int, str],
    n_control_users: int,
    n_event_users: int,
    lower: float,
    upper: float,
    min_series_len: int,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    config_id = stable_config_id(family, params)
    min_required = required_min_len(family, params)
    available = min_series_len >= min_required
    unavailable_reason = None if available else f"min_series_len={min_series_len} < required_min_len={min_required}"

    availability_row: Dict[str, Any] = {
        "family": family,
        "config_id": config_id,
        "params_json": json.dumps(params, sort_keys=True),
        "series_name": SERIES_NAME,
        "available": available,
        "unavailable_reason": unavailable_reason,
        "required_min_len": min_required,
        "observed_min_len": min_series_len,
    }

    control_alarm_count = 0
    event_alarm_count = 0
    nontrivial = False

    if available:
        for user_id, series in series_by_user.items():
            alarm = family_alarm(series, family, params)
            if alarm:
                nontrivial = True
                if label_by_user[user_id] == "control":
                    control_alarm_count += 1
                else:
                    event_alarm_count += 1

        control_fp = control_alarm_count / n_control_users if n_control_users > 0 else float("nan")
        event_alarm_rate = event_alarm_count / n_event_users if n_event_users > 0 else float("nan")
        accepted = bool(lower <= control_fp <= upper)
        distance = band_distance(control_fp, lower, upper)
    else:
        control_fp = float("nan")
        event_alarm_rate = float("nan")
        accepted = False
        distance = float("nan")

    calibration_row: Dict[str, Any] = {
        "family": family,
        "config_id": config_id,
        "params_json": json.dumps(params, sort_keys=True),
        "series_name": SERIES_NAME,
        "available": available,
        "unavailable_reason": unavailable_reason,
        "required_min_len": min_required,
        "observed_min_len": min_series_len,
        "control_alarm_count": control_alarm_count,
        "event_alarm_count": event_alarm_count,
        "n_control_users": n_control_users,
        "n_event_users": n_event_users,
        "control_fp": control_fp,
        "event_alarm_rate": event_alarm_rate,
        "accepted": accepted,
        "nontrivial": nontrivial,
        "band_distance": distance,
    }
    return availability_row, calibration_row


def sort_key_for_summary(row: Dict[str, Any]) -> Tuple[Any, ...]:
    available_penalty = 0 if bool(row["available"]) else 1
    distance = float(row["band_distance"]) if pd.notna(row["band_distance"]) else float("inf")
    event_alarm_count = -int(row["event_alarm_count"])
    control_alarm_count = int(row["control_alarm_count"])
    config_id = str(row["config_id"])
    return (available_penalty, distance, event_alarm_count, control_alarm_count, config_id)


def best_row(rows: List[Dict[str, Any]], *, nontrivial_only: bool = False) -> Dict[str, Any] | None:
    filtered = [row for row in rows if bool(row["available"]) and (not nontrivial_only or bool(row["nontrivial"]))]
    if not filtered:
        return None
    return sorted(filtered, key=sort_key_for_summary)[0]


def build_merged_summary(
    *,
    benchmark_freeze: Dict[str, Any],
    calibration_rows: List[Dict[str, Any]],
    counts: Dict[str, int],
    min_series_len: int,
) -> Dict[str, Any]:
    by_family: Dict[str, List[Dict[str, Any]]] = {}
    for row in calibration_rows:
        by_family.setdefault(str(row["family"]), []).append(row)

    families_summary: Dict[str, Any] = {}
    for family, rows in by_family.items():
        nearest = best_row(rows, nontrivial_only=False)
        nearest_nontrivial = best_row(rows, nontrivial_only=True)
        accepted_rows = [row for row in rows if bool(row["accepted"])]
        accepted_best = sorted(accepted_rows, key=sort_key_for_summary)[0] if accepted_rows else None

        families_summary[family] = {
            "n_configs": len(rows),
            "n_available_configs": sum(int(bool(row["available"])) for row in rows),
            "n_accepted_configs": sum(int(bool(row["accepted"])) for row in rows),
            "nearest": nearest,
            "nearest_nontrivial": nearest_nontrivial,
            "accepted_best": accepted_best,
        }

    payload = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "calibrate_slow_families",
        "benchmark_freeze_sha256": benchmark_freeze.get("benchmark_freeze_sha256"),
        "engine_hash": benchmark_freeze.get("frozen_contract", {}).get("engine_hash"),
        "series_name": SERIES_NAME,
        "counts": counts,
        "min_series_len": min_series_len,
        "equal_fp_band": benchmark_freeze.get("frozen_contract", {}).get("equal_fp_band"),
        "families": families_summary,
    }
    return payload


def write_outputs(
    paths: RepoPaths,
    availability_rows: List[Dict[str, Any]],
    calibration_rows: List[Dict[str, Any]],
    merged_summary: Dict[str, Any],
) -> Tuple[Path, Path, Path]:
    paths.results_manifests.mkdir(parents=True, exist_ok=True)

    availability_df = pd.DataFrame(availability_rows)
    calibration_df = pd.DataFrame(calibration_rows)

    availability_df.to_csv(paths.slow_availability_table_path, index=False)
    calibration_df.to_csv(paths.slow_calibration_matrix_path, index=False)

    merged_summary = dict(merged_summary)
    merged_summary["slow_merged_summary_sha256"] = json_sha256(merged_summary)
    paths.slow_merged_summary_path.write_text(
        json.dumps(merged_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return paths.slow_availability_table_path, paths.slow_calibration_matrix_path, paths.slow_merged_summary_path


def run(repo_root: Path) -> Tuple[Path, Path, Path]:
    paths = build_repo_paths(repo_root)
    benchmark_freeze, telemetry_panel = ensure_inputs(paths)
    series_by_user, label_by_user, counts, min_series_len = build_user_series(benchmark_freeze, telemetry_panel)

    lower = float(benchmark_freeze["frozen_contract"]["equal_fp_band"]["lower"])
    upper = float(benchmark_freeze["frozen_contract"]["equal_fp_band"]["upper"])
    n_control_users = int(counts["n_control_users"])
    n_event_users = int(counts["n_event_users"])

    availability_rows: List[Dict[str, Any]] = []
    calibration_rows: List[Dict[str, Any]] = []

    grids = slow_family_grids()
    total_configs = sum(len(v) for v in grids.values())
    done = 0
    print(f"[slow] calibrating {total_configs} slow-family configurations on {counts['n_users']:,} users")

    for family in ["matrix_profile", "permutation_entropy"]:
        configs = grids[family]
        print(f"[slow] family={family} configs={len(configs)}")
        for params in configs:
            availability_row, calibration_row = evaluate_config(
                family=family,
                params=params,
                series_by_user=series_by_user,
                label_by_user=label_by_user,
                n_control_users=n_control_users,
                n_event_users=n_event_users,
                lower=lower,
                upper=upper,
                min_series_len=min_series_len,
            )
            availability_rows.append(availability_row)
            calibration_rows.append(calibration_row)
            done += 1
            if done % 10 == 0 or done == total_configs:
                print(f"[slow] evaluated {done}/{total_configs} configs")

    merged_summary = build_merged_summary(
        benchmark_freeze=benchmark_freeze,
        calibration_rows=calibration_rows,
        counts=counts,
        min_series_len=min_series_len,
    )

    availability_path, calibration_path, merged_summary_path = write_outputs(
        paths,
        availability_rows,
        calibration_rows,
        merged_summary,
    )

    print(f"[ok] wrote slow availability table: {availability_path}")
    print(f"[ok] wrote slow calibration matrix: {calibration_path}")
    print(f"[ok] wrote slow merged summary:    {merged_summary_path}")
    return availability_path, calibration_path, merged_summary_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()