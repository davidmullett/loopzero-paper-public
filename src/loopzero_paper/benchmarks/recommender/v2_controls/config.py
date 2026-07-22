"""V2 controls pre-registration — frozen constants and paths.

All operative constants are LOADED from the frozen contract freeze (not hard-coded)
so the analysis provably traces to the frozen benchmark state. Pre-reg-specific
constants (t_split, window, budgets, seeds) are transcribed from the frozen Study-2
OSF pre-registration (osf.io/wka72; anchored at public commit 58721ac; PDF SHA-256
2374e370c0c35c404cc2fec0cce519127ed0045160ad566580e53f485e219df9), with the machine-readable
extract `results/v2_controls/wka72_registration_params.json` as the single source of truth
(guarded by `test_wka72_config_conformance.py`). The Study-1 document (osf.io/7bvgz) governs
ONLY the carried-over indicator/detector/fold definitions (§4); Study-2 supersedes it on the
budget grid (§6) and the population/control definition (§2). [R1 fix — the prior 7bvgz-only
citation was the documented root cause of the D-15 budget-grid nonconformance.]
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]

# ---- inputs (all read-only; frozen artifacts never written) ----
PANEL = REPO / "results/v2_prereg_slate_relog/movielens25m_recursive_frontier_public_v1__telemetry_panel__slate_v1.csv.gz"
MANIFEST = REPO / "results/manifests/movielens25m_recursive_frontier_public_v1__canonical_user_episode_manifest.csv"
CONTRACT = REPO / "results/frozen/movielens25m_recursive_frontier_public_v1__contract_freeze.json"
SORTED_RATINGS = REPO / "data/processed/movielens25m/ratings__sorted_by_user_time.csv.gz"
OUT_DIR = REPO / "results/v2_controls"

# ---- pre-reg constants (frozen doc) ----
T_SPLIT = 20                      # §4 landmark step
WINDOW = 20                       # §6 |W| (indicator window steps 1..20)
K = 10                            # §6 slate size
N_SLOTS = K * WINDOW              # §6 200 slate slots
BUDGETS = (0.02, 0.05, 0.10, 0.20)  # §6 (D-15 fix: Study-2 grid — 0.01 removed by design, 0.20 added)
PRIMARY_BUDGET = 0.05             # §6
BOOTSTRAP_ITERS = 10_000          # §8
BOOTSTRAP_SEED = 201              # §8/§13 comparison bootstrap
CONTROL_SEEDS = {                 # §10/§13
    "random": [101, 102, 103, 104, 105],        # 101 + {0..4}
    "shuffled_timestamp": [102 + i for i in range(5)],
    "mf_als": [103 + i for i in range(5)],
    "sequential": [104 + i for i in range(5)],
}
TSPLIT_SENSITIVITY = (15, 25)     # §4 reported-only

# ---- §11/§13 immutable guardrails (must never be altered under any framing) ----
GUARD_DELTA_TPR = 0.05            # §11 crit-1 threshold
GUARD_INCREMENTAL_AUC = 0.02     # §9/§11 threshold
POWER_MIN_EVAL_EVENTS = 200      # §11 power gate

# ---- deviations log (rulings recorded BEFORE any decision quantity) ----
# Timestamped by David 2026-07-13; see report. None alters a §11 criterion or §13 guardrail.
DEVIATIONS = {
    "flag_4_consecutive_misses_wording": "option(i) descriptive-wording correction, disclosed; L unchanged",
    "amber_1_log_activity": "warm_start_positive_count",       # §9 ruling
    "amber_2_pop_affinity_population": "all_162541_processed_users_LOUO",  # §9 ruling
    "note_4_detector_score": "family statistic maxed over <=20 window; alarm iff score>=threshold",
}


def load_frozen_constants() -> dict:
    c = json.loads(CONTRACT.read_text())
    col = c["collapse"]; eng = c["engine"]; hyp = eng["hyperparameters"]
    d = {
        "positive_rating_threshold": float(col["positive_rating_threshold"]),
        "warm_start_ratings": int(col["warm_start_ratings"]),
        "collapse_streak_len": int(col["collapse_streak_len"]),
        "remaining_frontier_floor": int(col["remaining_frontier_floor"]),
        "top_k": int(col["top_k"]),
        "max_horizon_steps": int(col["max_horizon_steps"]),
        "engine_hash": str(eng["engine_hash"]),
        "neighborhood_size": int(hyp["neighborhood_size"]),
        "min_common_raters": int(hyp["min_common_raters"]),
        "contract_sha256": str(c["contract_sha256"]),
    }
    # conformance asserts against the pre-reg's transcribed constants
    assert d["top_k"] == K, d
    assert d["max_horizon_steps"] == 50, d
    assert d["collapse_streak_len"] == 8, d
    assert d["remaining_frontier_floor"] == 10, d
    return d
