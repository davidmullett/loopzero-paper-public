"""Phase 2.5 — LABEL-SIDE dispositive-arm pre-census (I-10). BUILD ONLY this session.

For each dispositive arm — popularity-only (deterministic) and shuffled-timestamp
seeds 102+{0..4} (each individually, I-8) — rebuild §9 label-side under the frozen
rules and report, per eval fold: clean-control count, event count, the I-5a
LABEL-SIDE floor (>=100 clean controls AND >=100 events), and the realized k(b)
matched-budget table (control counts only).

EPISTEMIC SPLIT (stated in the artifact header, per I-10):
  * Label-side, READ here: frontier_size_after, label, collapse_step (same class as
    the Study-2 clean-control census).
  * In-block, NOT read here (deferred to Phase 3): G / p / δ, S, baseline detectors,
    ΔTPR, and the S-non-degeneracy (>=20 distinct S, IQR>0) half of the I-5a floor.

CAP-AND-RUN routing (I-10): a floor failure on any dispositive arm/seed does NOT end
the study — it CAPS the route set to {DIES, UNINTERPRETABLE-BY-CONTROL-ARM}. The cap
is declared and hash-anchored BEFORE the block runs; the block then determines which.
All arms clear the floor -> block runs unconstrained.

decision.RATIFIED stays False; this module is not executed until CP-2 authorizes it.
"""
from __future__ import annotations
import json
from typing import Dict, List
from . import config as C
from . import decision as D
from .controls import replay as R
from .controls.popularity_engine import PopularityRecommender
from .controls import shuffled_ts as STS

FLOOR_CLEAN_CONTROLS = 100      # I-5a label-side
FLOOR_EVENTS = 100              # I-5a label-side
SHUFFLED_TS_SEEDS = [102 + i for i in range(5)]   # I-8, each individually


def _fold_summary(units: List[R.LabelSideUnit]) -> Dict[str, dict]:
    out = {}
    for fd in ("cal", "eval"):
        sub = [u for u in units if u.fold == fd]
        events = sum(1 for u in sub if u.label == "event")
        controls = sum(1 for u in sub if u.label == "control")
        clean = sum(1 for u in sub if u.clean_control)
        out[fd] = {"n": len(sub), "events": events, "controls": controls, "clean_controls": clean}
    return out


def _arm_record(name: str, units: List[R.LabelSideUnit]) -> dict:
    fs = _fold_summary(units)
    ev = fs["eval"]
    floor_pass = ev["clean_controls"] >= FLOOR_CLEAN_CONTROLS and ev["events"] >= FLOOR_EVENTS
    kb = {str(b): int(round(b * ev["clean_controls"])) for b in D.BUDGETS}   # D-26: §6 matched k over eval CLEAN controls
    return {
        "arm": name,
        "by_fold": fs,
        "eval_clean_controls": ev["clean_controls"],
        "eval_events": ev["events"],
        "i5a_labelside_floor_pass": bool(floor_pass),
        "k_of_b_eval_controls": kb,
    }


def run(repo_root=C.REPO, *, out_path=None) -> dict:
    """Executes the pre-census. NOT called this session (build-only)."""
    ctx = R.load_context()
    bem_cfg, ct_cfg, traj, universe = ctx

    # rebuild the (order-independent) global CF index once, for the shuffled-TS arm
    from .. import compute_telemetry as ct   # pre_census is in v2_controls/ -> '..' == recommender
    from .. import build_user_episode_manifest as bem
    prov = json.loads((C.REPO / "results/manifests/movielens25m_recursive_frontier_public_v1__raw_input_provenance.json").read_text())
    ratings_df = bem.load_sorted_ratings(prov)
    _, user_pos, item_to_users, item_pos_counts = bem.build_user_trajectories_and_positive_index(
        ratings_df, positive_threshold=bem_cfg.positive_rating_threshold)
    seed_items = sorted({int(m) for items in user_pos.values() for m in items})
    cf_engine = STS.build_cf_engine(ct_cfg, user_pos, item_to_users, item_pos_counts,
                                    seed_movie_ids=seed_items, warm_cache=True)

    arms = []
    # popularity-only (deterministic; single replicate)
    pop = PopularityRecommender(item_pos_counts, bem_cfg.top_k)
    arms.append(_arm_record("popularity_only",
        R.run_arm_labelside(lambda uid: pop, traj, bem_cfg=bem_cfg, ct_cfg=ct_cfg, label="popularity")))
    # shuffled-TS seeds, each individually
    for s in SHUFFLED_TS_SEEDS:
        shuffled = STS.build_shuffled_trajectories(traj, s)
        arms.append(_arm_record(f"shuffled_ts_{s}",
            R.run_arm_labelside(lambda uid: cf_engine, shuffled, bem_cfg=bem_cfg, ct_cfg=ct_cfg, label=f"shuffledTS{s}")))

    all_clear = all(a["i5a_labelside_floor_pass"] for a in arms)
    report = {
        "stage": "phase25_labelside_pre_census",
        "epistemic_split": {
            "label_side_read": ["frontier_size_after", "label", "collapse_step"],
            "in_block_not_read": ["G", "p", "delta", "S", "baselines", "delta_tpr",
                                  "I-5a_S_non_degeneracy_half"],
        },
        "i5a_labelside_floor": {"clean_controls_ge": FLOOR_CLEAN_CONTROLS, "events_ge": FLOOR_EVENTS},
        "arms": arms,
        "all_arms_clear_floor": bool(all_clear),
        "route_cap": ("UNCONSTRAINED" if all_clear
                      else ["SIGNAL DIES", "UNINTERPRETABLE-BY-CONTROL-ARM"]),
        "decision_RATIFIED": D.RATIFIED,
    }
    out = out_path or (C.OUT_DIR / "phase25_pre_census.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main():
    raise SystemExit("Phase 2.5 pre-census is BUILD-ONLY until CP-2 authorizes it (do not run).")


if __name__ == "__main__":
    main()
