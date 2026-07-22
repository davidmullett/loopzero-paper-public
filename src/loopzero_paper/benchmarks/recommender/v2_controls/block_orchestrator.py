"""Phase 3 blind-block orchestrator. BUILD ONLY; guarded by decision.RATIFIED.

A single uninterrupted pass:  gates  ->  (on pass) §11 verdict via decision.verdict.

Invariants enforced here:
  * RATIFIED guard — refuses to run until CP-2 authorizes (decision.RATIFIED=True).
  * Route cap (I-10) — if the Phase 2.5 pre-census capped the route set, the block may
    not emit a route outside the cap (a SURVIVES under a cap is a hard error).
  * Hard-stop-on-gate-fail — if a construction/power gate fails, the block emits ONLY
    the gate verdict; NO decision quantity (ΔTPR / incremental AUC) is computed or
    written. Decision quantities are produced strictly after all gates pass.
  * Information boundary — nothing surfaces until the whole result is assembled and
    hashed; the caller receives only {verdict, reason, payload_sha256}. The full
    payload (with the decision quantities) is written to a gitignored, hash-anchored
    artifact — the number is embargoed; the hash + verdict are what leave the block.

The real-engine SUMMARY PRODUCER (compute_summaries) is a separate, RATIFIED-guarded
function; the orchestration logic below is pure and is exercised by the verdict test
suite. This module is never executed until CP-2 authorizes it.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import List, Optional
from . import config as C
from . import decision as D

# Gate routes are upstream of the control-arm stage (real-arm PC1/PC2/power), so they are
# ALWAYS reachable regardless of a Phase-2.5 route cap. The cap forecloses SIGNAL SURVIVES.
_GATE_ROUTES = frozenset({"INDETERMINATE-BY-POWER", "UNINTERPRETABLE-BY-CONSTRUCTION"})


def _hash_payload(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _verify_cap_artifact(cap_artifact, cap_artifact_sha256) -> Optional[List[str]]:
    """I-10 precondition: the block REQUIRES the anchored Phase-2.5 pre-census cap artifact.
    Recompute its SHA-256, refuse unless it matches the committed anchor, and DERIVE the
    route cap from the verified artifact (so the enforced cap is exactly the anchored one).
    Refuses if the artifact or its anchored hash is absent, or on any mismatch."""
    if cap_artifact is None or cap_artifact_sha256 is None:
        raise RuntimeError(
            "cap-artifact precondition (I-10): the Phase-2.5 pre-census cap artifact AND its "
            "anchored SHA-256 are REQUIRED before the block may run.")
    p = Path(cap_artifact)
    if not p.exists():
        raise RuntimeError(f"cap-artifact precondition: artifact not found at {p}")
    live = hashlib.sha256(p.read_bytes()).hexdigest()
    if live != cap_artifact_sha256:
        raise RuntimeError(
            f"cap-artifact precondition: hash mismatch — live {live[:12]}… != anchored "
            f"{cap_artifact_sha256[:12]}…; the cap is not the anchored one.")
    rc = json.loads(p.read_text()).get("route_cap")
    return None if rc == "UNCONSTRAINED" else rc


def compute_summaries(*args, **kwargs):
    """Phase 3 real-engine producer: rebuild real + control arms and summarise them into
    (RealArm, popularity ControlArm, [shuffled ControlArm x5]) — ΔTPR per budget (sweep +
    cluster BCa with I-6 re-max), §9 covariate signs + incremental AUC, and each arm's
    measurability + criterion-1 bar. Held behind RATIFIED; runs only in Phase 3."""
    if not D.RATIFIED:
        raise RuntimeError("HELD: real-engine summary production requires decision.RATIFIED=True (CP-2).")
    import numpy as np
    from . import producer as PR
    from . import covariates as COV
    from . import conformance as CF
    # E (before any computation): the three inputs must match their CONTENT (decompressed) pins.
    CF.input_gate()
    real_units = PR.load_arm_units(C.PANEL)                                   # real slate panel (parse only)
    # F (before any decision quantity): loaded population verified against the anchored census
    # (count + per-class per-fold set-hash), census cross-checked vs registration, k derived from census.
    CF.assert_population_conformance(real_units)
    # §9 covariates READ from the precomputed, anchored cache (data prep) — NOT computed
    # first-time-at-scale inside the block. Definitions unchanged (I-1 log_activity, I-2 pop_affinity).
    cov = COV.load_real_covariates()
    la = np.array([cov[int(u)][0] for u in real_units.user_id], float)
    pa = np.array([cov[int(u)][1] for u in real_units.user_id], float)
    real = PR.real_arm(real_units, la, pa)
    pop = PR.control_arm("popularity", PR.load_arm_units(C.OUT_DIR / "arm_popularity_only__slate_panel.csv.gz"))
    shuffled = [PR.control_arm(f"shuffled_ts_{102 + i}",
                               PR.load_arm_units(C.OUT_DIR / f"arm_shuffled_ts_{102 + i}__slate_panel.csv.gz"))
                for i in range(5)]
    return real, pop, shuffled


def run_block(real: D.RealArm, popularity: D.ControlArm, shuffled_seeds: List[D.ControlArm],
              *, cap_artifact, cap_artifact_sha256, out_path=None) -> dict:
    """Single uninterrupted pass. The route cap is DERIVED from the anchored Phase-2.5
    pre-census cap artifact (verified by SHA-256 against `cap_artifact_sha256`); the block
    refuses to run without it (I-10, enforced not operational). Returns only
    {verdict, reason, payload_sha256}; the decision quantities live in the hashed,
    gitignored payload artifact."""
    if not D.RATIFIED:
        raise RuntimeError("HELD: the Phase 3 block must not run until CP-2 sets decision.RATIFIED=True.")

    # I-10 precondition: cap must be anchored BEFORE the block — verify then derive it.
    route_cap = _verify_cap_artifact(cap_artifact, cap_artifact_sha256)

    # --- gates first; hard-stop WITHOUT computing/writing any decision quantity ---
    if not real.power_ok:
        return _finalize(D._res("INDETERMINATE-BY-POWER",
                                f"eval events {real.eval_events} < {C.POWER_MIN_EVAL_EVENTS}"),
                         payload=None, route_cap=route_cap, out_path=out_path)
    if not real.pc1_pass:
        return _finalize(D._res("UNINTERPRETABLE-BY-CONSTRUCTION", "PC1 learnability gate fails (I-7)"),
                         payload=None, route_cap=route_cap, out_path=out_path)
    if not real.pc2_pass:
        return _finalize(D._res("UNINTERPRETABLE-BY-CONSTRUCTION", "PC2 liveness gate fails (S degenerate)"),
                         payload=None, route_cap=route_cap, out_path=out_path)

    # --- gates passed: NOW the decision quantities are in scope; compute the verdict ---
    result = D.verdict(real, popularity, shuffled_seeds)
    payload = {
        "verdict": result["verdict"], "reason": result["reason"],
        "criteria": result.get("criteria"),
        "real_delta_by_budget": {str(b): real.delta_by_budget[b] for b in D.BUDGETS},
        "covariate": {"bG": real.cov_bG, "bP": real.cov_bP, "bD": real.cov_bD, "incr_auc": real.cov_incr_auc},
        "popularity_delta_b05": popularity.delta_b05,
        "shuffled_delta_b05": {s.name: s.delta_b05 for s in shuffled_seeds},
    }
    return _finalize(result, payload=payload, route_cap=route_cap, out_path=out_path)


def _finalize(result: dict, *, payload, route_cap, out_path) -> dict:
    verdict = result["verdict"]
    # Route-cap enforcement (I-10): under a cap, the block cannot emit a control-arm-stage
    # verdict outside the cap. Gate routes (power/PC1/PC2) are upstream and always allowed;
    # the cap's operative effect is to foreclose SIGNAL SURVIVES.
    if route_cap is not None and verdict not in (set(route_cap) | _GATE_ROUTES):
        raise AssertionError(f"route-cap violation: verdict {verdict!r} not in anchored cap {route_cap}")
    full = {"verdict": verdict, "reason": result["reason"], "route_cap": route_cap,
            "decision_quantities": payload}   # payload is None on a gate hard-stop
    payload_hash = _hash_payload(full)
    if out_path is not None:
        out_path.write_text(json.dumps({**full, "payload_sha256": payload_hash}, indent=2, sort_keys=True) + "\n")
    # Information boundary: only the verdict + hash leave the block.
    return {"verdict": verdict, "reason": result["reason"], "payload_sha256": payload_hash}
