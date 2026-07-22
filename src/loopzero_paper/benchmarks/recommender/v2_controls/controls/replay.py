"""§10 control-arm replay — drives the FROZEN replay functions with a control engine.

Reuses `build_user_episode_manifest.simulate_user_episode` (labeling + inclusion)
and `compute_telemetry.simulate_user_telemetry` (per-step slates) unchanged, so the
warm-start, deterministic frontier-reveal, and 8-consecutive-miss/floor-10 collapse
rules are reproduced EXACTLY. Each arm rebuilds its own slates, labels, and landmark
population L2. Label-side and slate-side come from the SAME identically-seeded engine
(two fresh instances, one per replay) so they stay consistent (the engine is stateless).
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np

from ... import build_user_episode_manifest as bem
from ... import compute_telemetry as ct
from .. import config as C
from .. import indicators as I
from .. import baselines as B
from ..population import fold
from .random_engine import RandomRecommender

STREAK = 8  # collapse_streak_len (asserted against contract below)


@dataclass
class ArmUnit:
    user_id: int
    fold: str
    label: str                       # 'event' | 'control'
    collapse_step: Optional[int]
    G: float = 0.0
    p: float = 0.0
    delta: float = 0.0
    pc1: float = 0.0
    miss_run_fraction: List[float] = field(default_factory=list)
    clean_control: bool = False      # control never starved through 50 (for I-5a clean-control count)


def load_context():
    """Frozen cfgs (both flavours) + trajectories + item universe. Asserts contract constants."""
    contract = json.loads((C.REPO / "results/frozen/movielens25m_recursive_frontier_public_v1__contract_freeze.json").read_text())
    bench = json.loads((C.REPO / "results/frozen/movielens25m_recursive_frontier_public_v1__benchmark_freeze_state.json").read_text())
    bem_cfg = bem.parse_config(contract)
    ct_cfg = ct.parse_config(contract, bench)
    # hard asserts against the frozen contract (I-2/§3)
    assert bem_cfg.warm_start_ratings == 30 and bem_cfg.collapse_streak_len == STREAK
    assert bem_cfg.remaining_frontier_floor == 10 and bem_cfg.max_horizon_steps == 50
    assert bem_cfg.top_k == 10 and float(bem_cfg.positive_rating_threshold) == 4.0
    prov = json.loads((C.REPO / "results/manifests/movielens25m_recursive_frontier_public_v1__raw_input_provenance.json").read_text())
    ratings_df = bem.load_sorted_ratings(prov)
    traj, user_pos, item_to_users, item_pos_counts = bem.build_user_trajectories_and_positive_index(
        ratings_df, positive_threshold=bem_cfg.positive_rating_threshold)
    universe = np.array(sorted(int(x) for x in item_to_users.keys()), dtype=np.int64)
    return bem_cfg, ct_cfg, traj, universe


def replay_user(traj, *, bem_cfg, ct_cfg, universe, arm_seed) -> Optional[ArmUnit]:
    """Full frozen replay for one user under the random engine; None if excluded / not in L2."""
    eng_l = RandomRecommender(universe, bem_cfg.top_k, traj.user_id, arm_seed)
    ep = bem.simulate_user_episode(traj, cfg=bem_cfg, engine=eng_l)
    if ep.inclusion_status != "included":
        return None
    cs = ep.collapse_step
    in_L2 = (ep.label == "control") or (ep.label == "event" and cs is not None and 20 < cs <= 50)
    if not in_L2:
        return None
    meta = ct.EpisodeMeta(
        user_id=traj.user_id, label=ep.label, collapse_step=cs,
        natural_alarm_window_start_step=int(ep.natural_alarm_window_start_step),
        natural_alarm_window_end_step=int(ep.natural_alarm_window_end_step))
    eng_t = RandomRecommender(universe, bem_cfg.top_k, traj.user_id, arm_seed)  # fresh, same seed
    rows = ct.simulate_user_telemetry(traj, meta, cfg=ct_cfg, engine=eng_t)
    win = [r for r in rows if 1 <= int(r["step"]) <= C.WINDOW]
    if len(win) < C.WINDOW:
        return None  # incomplete window (should not happen for L2 by construction)
    win.sort(key=lambda r: int(r["step"]))
    slates = [json.loads(r["slate_json"]) for r in win]
    mrf = [min(1.0, int(r["consecutive_misses_after_step"]) / STREAK) for r in win]
    pc1 = sum(1 for r in win if int(r["hit_this_step"]) == 0) / C.WINDOW
    g, p, d = I.churn_G(slates), I.occupancy_p(slates), I.coverage_delta(slates)
    # clean control (for I-5a): control whose frontier never starves through step 50
    clean = False
    if ep.label == "control":
        clean = all(int(r["frontier_size_after"]) >= bem_cfg.remaining_frontier_floor
                    for r in rows if int(r["step"]) > C.WINDOW)
    return ArmUnit(user_id=traj.user_id, fold=fold(traj.user_id), label=ep.label,
                   collapse_step=cs, G=g, p=p, delta=d, pc1=pc1, miss_run_fraction=mrf,
                   clean_control=clean)


def run_arm(arm_seed: int, *, ctx, user_ids=None, log_every=5000) -> List[ArmUnit]:
    bem_cfg, ct_cfg, traj, universe = ctx
    ids = list(traj.keys()) if user_ids is None else list(user_ids)
    ids.sort()
    units: List[ArmUnit] = []
    for n, uid in enumerate(ids, 1):
        u = replay_user(traj[uid], bem_cfg=bem_cfg, ct_cfg=ct_cfg, universe=universe, arm_seed=arm_seed)
        if u is not None:
            units.append(u)
        if log_every and n % log_every == 0:
            print(f"[arm {arm_seed}] {n}/{len(ids)} users  L2={len(units)}", flush=True)
    return units


# =====================================================================================
# LABEL-SIDE ONLY replay for the Phase 2.5 pre-census (I-10). Reads exclusively label-side
# fields (label, collapse_step, frontier_size_after); NEVER reads slate_json / G / p / δ /
# S / baselines. Same epistemic class as the Study-2 clean-control census. `make_engine`
# is a callable user_id -> engine (a fresh RandomRecommender per user, or the shared
# stateless popularity / canonical-CF engine).
# =====================================================================================
@dataclass
class LabelSideUnit:
    user_id: int
    fold: str
    label: str                 # 'event' | 'control'
    collapse_step: Optional[int]
    clean_control: bool         # control whose frontier never drops below the floor through step 50


def replay_user_labelside(traj, *, bem_cfg, ct_cfg, make_engine) -> Optional["LabelSideUnit"]:
    eng_l = make_engine(traj.user_id)
    ep = bem.simulate_user_episode(traj, cfg=bem_cfg, engine=eng_l)
    if ep.inclusion_status != "included":
        return None
    cs = ep.collapse_step
    in_L2 = (ep.label == "control") or (ep.label == "event" and cs is not None and 20 < cs <= 50)
    if not in_L2:
        return None
    meta = ct.EpisodeMeta(
        user_id=traj.user_id, label=ep.label, collapse_step=cs,
        natural_alarm_window_start_step=int(ep.natural_alarm_window_start_step),
        natural_alarm_window_end_step=int(ep.natural_alarm_window_end_step))
    eng_t = make_engine(traj.user_id)
    rows = ct.simulate_user_telemetry(traj, meta, cfg=ct_cfg, engine=eng_t)
    # LABEL-SIDE READ ONLY: frontier_size_after + step. No slate/indicator/S/baseline access.
    clean = (ep.label == "control") and all(
        int(r["frontier_size_after"]) >= bem_cfg.remaining_frontier_floor
        for r in rows if int(r["step"]) > C.WINDOW)
    return LabelSideUnit(user_id=int(traj.user_id), fold=fold(traj.user_id),
                         label=ep.label, collapse_step=cs, clean_control=bool(clean))


def run_arm_labelside(make_engine, trajectories, *, bem_cfg, ct_cfg, user_ids=None, log_every=5000, label=""):
    ids = sorted(trajectories.keys()) if user_ids is None else sorted(user_ids)
    units = []
    for n, uid in enumerate(ids, 1):
        u = replay_user_labelside(trajectories[uid], bem_cfg=bem_cfg, ct_cfg=ct_cfg, make_engine=make_engine)
        if u is not None:
            units.append(u)
        if log_every and n % log_every == 0:
            print(f"[labelside {label}] {n}/{len(ids)}  L2={len(units)}", flush=True)
    return units
