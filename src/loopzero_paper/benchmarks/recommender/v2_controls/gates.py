"""§4 WHOLE-L validity diagnostics — non-decision quantities (authorized to run pre-ratification).

RELABEL (D-27): these gates are computed over the WHOLE-L population (ALL controls) and are §4
diagnostics — they are NOT the registered §5/§6 operating points. `pc1_gate`'s TPR is over all
eval-L controls (the Study-1 pathology quantity published as D-2), not over the CLEAN population.
The registered PC1/PC2 gates and §6 matched counts are computed ONLY in the block
(producer.py / block_orchestrator.py) over the CLEAN population — the clean-population gate lives
there and nowhere else. Assertion (B) in the conformance suite enforces this by structure.

power_gate  — §11: eval-fold events in L >= 200 else INDETERMINATE-BY-POWER.
pc2_gate    — whole-L δ liveness: >=20 distinct values across L and IQR>0 (indicator-only).
pc1_gate    — whole-L PC1 early-miss TPR at the primary budget on the eval fold (ALL controls; D-2).

PC1-gate wording flag: §7 says "exceed chance TPR ... (BCa 95% CI for TPR − prevalence
excluding 0)". 'chance TPR' vs 'prevalence' are inconsistent: a no-skill detector at a
b control-budget scores event-TPR ≈ b (=0.05), whereas event-class prevalence in L ≈ 0.81
makes TPR−prevalence structurally < 0 (unpassable). We report the underlying TPR + CI and
BOTH candidate references; the pass/fail rule awaits ratification of 'chance TPR'.
"""
from __future__ import annotations
from typing import Dict, List
import numpy as np
from . import config as C
from . import indicators as I
from . import baselines as B
from . import sweep as S
from .bootstrap import bca_ci
from .population import Unit


def power_gate(eval_events_in_L: int) -> dict:
    return {
        "eval_events_in_L": eval_events_in_L,
        "threshold": C.POWER_MIN_EVAL_EVENTS,
        "pass": eval_events_in_L >= C.POWER_MIN_EVAL_EVENTS,
        "verdict": "OK" if eval_events_in_L >= C.POWER_MIN_EVAL_EVENTS else "INDETERMINATE-BY-POWER",
    }


def pc2_gate(L: List[Unit]) -> dict:
    deltas = np.array([I.coverage_delta(u.slates) for u in L], float)
    q75, q25 = np.percentile(deltas, [75, 25])
    iqr = float(q75 - q25)
    n_distinct = int(np.unique(deltas).size)
    return {
        "n_distinct_delta_values_over_L": n_distinct,
        "delta_IQR": iqr,
        "pass": bool(n_distinct >= 20 and iqr > 0),
        "criterion": "delta >=20 distinct values across L AND IQR>0",
    }


def pc1_gate(L: List[Unit]) -> dict:
    """PC1 = early miss rate; matched-count TPR at b=0.05 on eval fold + BCa CI."""
    evalL = [u for u in L if u.fold == "eval"]
    score = np.array([B.pc1_early_miss_rate(u.hit) for u in evalL], float)
    is_event = np.array([u.label == "event" for u in evalL], bool)
    user_id = np.array([u.user_id for u in evalL])
    n_controls = int((~is_event).sum())
    count = S.matched_count(C.PRIMARY_BUDGET, n_controls)
    prevalence = float(is_event.mean())

    def tpr_stat(idx: np.ndarray) -> float:
        ie = is_event[idx]
        nc = int((~ie).sum())
        cnt = S.matched_count(C.PRIMARY_BUDGET, nc)
        return S.matched_tpr(score[idx], ie, user_id[idx], cnt)

    tpr, tpr_lo, tpr_hi = bca_ci(len(evalL), tpr_stat, n_boot=C.BOOTSTRAP_ITERS, seed=C.BOOTSTRAP_SEED)

    # gate under the two candidate references (flag): chance=b vs prevalence
    chance_b = C.PRIMARY_BUDGET
    return {
        "primary_budget": C.PRIMARY_BUDGET,
        "matched_control_alarm_count": count,
        "n_eval_controls": n_controls,
        "event_prevalence_eval_L": round(prevalence, 4),
        "PC1_TPR_at_b05": round(tpr, 6),
        "PC1_TPR_BCa95": [round(tpr_lo, 6), round(tpr_hi, 6)],
        "reading_chance_equals_b": {
            "reference": chance_b,
            "TPR_minus_ref": round(tpr - chance_b, 6),
            "pass_if_CI_excludes_0": bool(tpr_lo > chance_b),
        },
        "reading_literal_prevalence": {
            "reference": round(prevalence, 4),
            "TPR_minus_ref": round(tpr - prevalence, 6),
            "pass_if_CI_excludes_0": bool(tpr_lo > prevalence),
        },
        "WORDING_FLAG": "PC1-gate reference ambiguous ('chance TPR' vs 'prevalence'); verdict pending ratification. Only 'chance=b' yields a sensible (passable) gate.",
    }
