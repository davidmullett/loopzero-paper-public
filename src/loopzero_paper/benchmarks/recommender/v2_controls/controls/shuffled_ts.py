"""§10 dispositive control — SHUFFLED-TIMESTAMP arm (recursion falsifier).

NOT an engine swap: the CANONICAL item-item CF engine is run on data whose per-user
event order is (seeded) shuffled, breaking the chronological contract while holding
the marginals fixed. Because the global CF index (item_to_users, item_positive_counts,
user_positive_items) is order-independent, it is built ONCE and reused across all five
seeds; only each user's warm-start prefix and frontier reveal order change. Seeds
102 + {0..4}, each replicate individually (I-8).
"""
from __future__ import annotations
from typing import Dict
import numpy as np

from ... import build_user_episode_manifest as bem
from ... import compute_telemetry as ct


def shuffle_trajectory(traj, arm_seed: int):
    """Return a UserTrajectory with the user's events permuted by a seed keyed ONLY on
    (arm_seed, user_id) — §4-safe: the permutation depends on no step outcome."""
    n = int(len(traj.movie_ids))
    rng = np.random.default_rng([int(arm_seed), int(traj.user_id)])
    perm = rng.permutation(n)
    return bem.UserTrajectory(
        user_id=int(traj.user_id),
        movie_ids=np.asarray(traj.movie_ids)[perm].copy(),
        ratings=np.asarray(traj.ratings)[perm].copy(),
        timestamps=np.asarray(traj.timestamps)[perm].copy(),
    )


def build_shuffled_trajectories(base_trajectories: Dict[int, object], arm_seed: int) -> Dict[int, object]:
    return {uid: shuffle_trajectory(t, arm_seed) for uid, t in base_trajectories.items()}


def build_cf_engine(ct_cfg, user_positive_items, item_to_users, item_positive_counts,
                    *, seed_movie_ids=None, warm_cache: bool = True):
    """Construct the frozen canonical item-item CF engine from the (order-independent)
    global index. Reused across all shuffled-TS seeds. Heavy (neighbor-cache warming) —
    built here; RUN only in Phase 3."""
    engine = ct.FrozenItemItemCFEngine(
        user_positive_items=user_positive_items,
        item_to_users=item_to_users,
        item_positive_counts=item_positive_counts,
        neighborhood_size=ct_cfg.neighborhood_size,
        min_common_raters=ct_cfg.min_common_raters,
        top_k=ct_cfg.top_k,
        tie_break_rule=ct_cfg.tie_break_rule,
    )
    if warm_cache and seed_movie_ids is not None:
        engine.warm_neighbor_cache(seed_movie_ids, progress_every=500)
    return engine
