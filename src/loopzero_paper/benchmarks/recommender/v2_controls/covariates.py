"""§9 covariate adjustment — BUILD ONLY (feeds the HELD incremental-AUC criterion).

Rulings applied (deviations log, 2026-07-13):
  AMBER-1: log_activity = log(1 + warm_start_positive_count)   [manifest column]
  AMBER-2: pop_affinity popularity counted over ALL 162,541 processed users, LOUO.

Excluded by name (§9): steps_to_collapse, aligned_step, is_precollapse_window,
and any other label-derived column. warm-start-prefix-length dropped (degenerate).

pop_affinity requires a raw re-ingest of pre-episode profile items (not persisted
in the panel). Implemented here; RUN only in the covariate/decision phase.
"""
from __future__ import annotations
import csv, gzip, math
from typing import Dict, List, Set
from collections import Counter
from . import config as C

LABEL_DERIVED_EXCLUDED = {"steps_to_collapse", "aligned_step", "is_precollapse_window",
                          "collapse_step", "consecutive_misses_after_step"}


def log_activity_from_manifest() -> Dict[int, float]:
    """log_activity = log(1 + warm_start_positive_count) per user (AMBER-1)."""
    out: Dict[int, float] = {}
    with open(C.MANIFEST) as f:
        r = csv.DictReader(f)
        for row in r:
            u = int(row["user_id"])
            out[u] = math.log(1.0 + float(row["warm_start_positive_count"]))
    return out


def build_pre_episode_profiles() -> Dict[int, List[int]]:
    """Reconstruct each processed user's pre-episode profile items from raw sorted
    ratings: first `warm_start_ratings` chronological ratings with rating >= threshold.
    Over ALL processed users (AMBER-2 population). Heavy: full pass over 25M rows."""
    k = C.load_frozen_constants()
    warm = k["warm_start_ratings"]; thr = k["positive_rating_threshold"]
    seen_counts: Dict[int, int] = {}
    profiles: Dict[int, List[int]] = {}
    with gzip.open(C.SORTED_RATINGS, "rt", newline="") as f:
        r = csv.reader(f); next(r)  # header userId,movieId,rating,timestamp
        for uid_s, mid_s, rat_s, _ in r:
            u = int(uid_s)
            c = seen_counts.get(u, 0)
            if c >= warm:
                continue
            seen_counts[u] = c + 1
            if float(rat_s) >= thr:
                profiles.setdefault(u, []).append(int(mid_s))
    return profiles


def pop_affinity(profiles: Dict[int, List[int]]) -> Dict[int, float]:
    """pop_affinity_u = mean over u's profile items of log(1 + #OTHER users whose
    pre-episode profile contains the item), LOUO (AMBER-2)."""
    item_users: Counter = Counter()
    for items in profiles.values():
        for i in set(items):
            item_users[i] += 1
    out: Dict[int, float] = {}
    for u, items in profiles.items():
        uniq = set(items)
        if not uniq:
            out[u] = 0.0
            continue
        vals = [math.log(1.0 + (item_users[i] - 1)) for i in uniq]  # LOUO: subtract self
        out[u] = sum(vals) / len(vals)
    return out


def load_real_covariates(path=None):
    """Read the PRECOMPUTED, anchored real-covariate cache (data prep; I-1/I-2 defns
    unchanged). Returns {user_id: (log_activity, pop_affinity)}. compute_summaries reads
    this instead of running log_activity / the pop_affinity LOUO re-ingest at block time."""
    import gzip, csv
    from . import config as C
    p = path or (C.OUT_DIR / "real_covariates.csv.gz")
    out = {}
    with gzip.open(p, "rt", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            out[int(row["user_id"])] = (float(row["log_activity"]), float(row["pop_affinity"]))
    return out
