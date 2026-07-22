"""§11 Study-2 verdict logic — PURE functions of already-summarised arm inputs.

Encodes the frozen §11 four-criteria decision plus the ratified execution
interpretations I-5(rev), I-5a, I-5b, I-6, I-7, I-8. Every function here is a pure
function of pre-computed summaries (ΔTPR point+CI, gate booleans, measurability
counts) — it computes NO indicator×label quantity itself. Running the pipeline that
FEEDS these on real-engine data is Phase 3 (gated by RATIFIED); the logic below is
validated on synthetic known-answer cases with RATIFIED=False.

Verdict route lattice (ratified C4-dominance ruling, 2026-07-17), top to bottom:
  (i)   power gate                             -> INDETERMINATE-BY-POWER
        PC1 / PC2 gate fail                    -> UNINTERPRETABLE-BY-CONSTRUCTION
  (ii)  any of criteria 1-3 fails             -> SIGNAL DIES  (regardless of any arm's
                                                 measurability; a real-engine null cannot
                                                 hide behind UNINTERPRETABLE)
  (iii) 1-3 hold AND any MEASURABLE dispositive arm/seed meets the criterion-1 bar (retains)
                                              -> SIGNAL DIES  (criterion 4 failed; measurable
                                                 retention DOMINATES unmeasurability)
  (iv)  1-3 hold AND no measurable retention AND any dispositive arm/seed unmeasurable
                                              -> UNINTERPRETABLE-BY-CONTROL-ARM
  (v)   1-3 hold AND all dispositive arms/seeds measurable AND criterion-1 bar unmet on
        popularity and on all five shuffled seeds -> SIGNAL SURVIVES
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from . import config as C

# Real-engine execution (Phase 3) gate. The verdict LOGIC below is pure and testable
# on synthetic inputs; only feeding it real-engine indicator×label quantities is held.
RATIFIED = False

BUDGETS = (0.02, 0.05, 0.10, 0.20)     # §6/§10 (D-15 fix: Study-2 grid; criterion_2 counts >=3 of these 4)
PRIMARY_BUDGET = 0.05
DELTA = C.GUARD_DELTA_TPR              # 0.05, §13 immutable
INCR_AUC = C.GUARD_INCREMENTAL_AUC     # 0.02, §13 immutable
N_SHUFFLED_SEEDS = 5                    # I-8: 102 + {0..4}

CI = Tuple[float, float, float]        # (point, lo, hi)


def ci_excludes_zero(lo: float, hi: float) -> bool:
    return lo > 0.0 or hi < 0.0


def bar_met(d: CI) -> bool:
    """§11 criterion-1 bar for an arm: ΔTPR point >= 0.05 AND BCa 95% CI excludes 0."""
    point, lo, hi = d
    return point >= DELTA and ci_excludes_zero(lo, hi)


def is_measurable(n_clean_controls: int, n_events: int, s_distinct: int, s_iqr: float) -> bool:
    """I-5a: eval fold >= 100 clean controls, >= 100 events, S non-degenerate."""
    return n_clean_controls >= 100 and n_events >= 100 and s_distinct >= 20 and s_iqr > 0.0


def pc1_gate_pass(tpr_minus_b: CI) -> bool:
    """I-7: PC1 chance = b; gate = (TPR_PC1 - 0.05) > 0 AND BCa CI of the difference excludes 0."""
    point, lo, hi = tpr_minus_b
    return point > 0.0 and lo > 0.0


def covariate_pass(bG: CI, bP: CI, bD: CI, incr_auc: CI) -> bool:
    """§9: sign(bG)>0, sign(bP)>0, sign(bD)<0 each with BCa CI excluding 0; AND
    incremental AUC >= 0.02 with BCa CI excluding 0."""
    signs = (bG[1] > 0.0) and (bP[1] > 0.0) and (bD[2] < 0.0)      # bG lo>0, bP lo>0, bD hi<0
    incr = (incr_auc[0] >= INCR_AUC) and (incr_auc[1] > 0.0)
    return signs and incr


@dataclass
class ControlArm:
    name: str
    n_clean_controls: int
    n_events: int
    s_distinct: int
    s_iqr: float
    delta_b05: CI                       # ΔTPR at b=0.05 on this arm's OWN rebuilt population
    tpr_s_minus_b: Optional[CI] = None  # I-5b absolute S discrimination (reporting-only)

    @property
    def measurable(self) -> bool:
        return is_measurable(self.n_clean_controls, self.n_events, self.s_distinct, self.s_iqr)

    @property
    def crit1_bar_met(self) -> bool:    # I-5rev
        return bar_met(self.delta_b05)


@dataclass
class RealArm:
    eval_events: int
    pc1_minus_b: CI
    pc2_pass: bool
    delta_by_budget: Dict[float, CI]
    cov_bG: CI
    cov_bP: CI
    cov_bD: CI
    cov_incr_auc: CI

    @property
    def power_ok(self) -> bool:
        return self.eval_events >= C.POWER_MIN_EVAL_EVENTS

    @property
    def pc1_pass(self) -> bool:
        return pc1_gate_pass(self.pc1_minus_b)

    @property
    def crit1(self) -> bool:
        return bar_met(self.delta_by_budget[PRIMARY_BUDGET])

    @property
    def crit2(self) -> bool:
        return sum(1 for b in BUDGETS if self.delta_by_budget[b][0] > 0.0) >= 3

    @property
    def crit3(self) -> bool:
        return covariate_pass(self.cov_bG, self.cov_bP, self.cov_bD, self.cov_incr_auc)


def _res(verdict: str, reason: str, **extra) -> dict:
    return {"verdict": verdict, "reason": reason, **extra}


def i5b_absolute_flags(control_arms: List[ControlArm]) -> Dict[str, bool]:
    """I-5b (reporting-only): does S beat chance (TPR_S - b, CI excl 0) on a severed arm?"""
    out = {}
    for a in control_arms:
        out[a.name] = bool(a.tpr_s_minus_b is not None
                           and a.tpr_s_minus_b[0] > 0.0 and a.tpr_s_minus_b[1] > 0.0)
    return out


def verdict(real: RealArm, popularity: ControlArm, shuffled_seeds: List[ControlArm]) -> dict:
    """Return {'verdict', 'reason', ...}. Pure; no indicator×label computation."""
    assert len(shuffled_seeds) == N_SHUFFLED_SEEDS, "I-8 requires exactly 5 shuffled-TS seeds"

    if not real.power_ok:
        return _res("INDETERMINATE-BY-POWER",
                    f"eval events {real.eval_events} < {C.POWER_MIN_EVAL_EVENTS}")
    if not real.pc1_pass:
        return _res("UNINTERPRETABLE-BY-CONSTRUCTION", "PC1 learnability gate fails (I-7)")
    if not real.pc2_pass:
        return _res("UNINTERPRETABLE-BY-CONSTRUCTION", "PC2 liveness gate fails (S degenerate)")

    c1, c2, c3 = real.crit1, real.crit2, real.crit3
    if not (c1 and c2 and c3):
        return _res("SIGNAL DIES", f"fails on own merits: c1={c1} c2={c2} c3={c3}",
                    criteria={"c1": c1, "c2": c2, "c3": c3})

    # Dispositive arms (I-5rev / I-8): popularity + the five shuffled-TS seeds.
    dispositive = [("popularity", popularity)] + [(s.name, s) for s in shuffled_seeds]

    # (iii) C4 DOMINANCE: any MEASURABLE dispositive arm/seed that RETAINS S's advantage
    #       (meets the criterion-1 bar) fails criterion 4 -> DIES. This dominates step (iv):
    #       a confirmed non-specific signal is not rescued to UNINTERPRETABLE just because a
    #       separate arm happens to be unmeasurable.
    retained = [name for name, a in dispositive if a.measurable and a.crit1_bar_met]
    if retained:
        return _res("SIGNAL DIES", f"criterion 4 fails; S retained its advantage on: {retained}",
                    criteria={"c1": c1, "c2": c2, "c3": c3, "c4": False})

    # (iv) no measurable retention, but specificity cannot be completed because a dispositive
    #      arm/seed is unmeasurable (I-5a / I-8).
    unmeasurable = [name for name, a in dispositive if not a.measurable]
    if unmeasurable:
        return _res("UNINTERPRETABLE-BY-CONTROL-ARM",
                    f"criteria 1-3 hold, no measurable retention, unmeasurable dispositive arm(s): {unmeasurable}")

    # (v) all dispositive arms/seeds measurable, none retained -> criterion 4 met -> SURVIVES.
    return _res("SIGNAL SURVIVES", "all four criteria met; recursion/personalization specificity confirmed",
                criteria={"c1": c1, "c2": c2, "c3": c3, "c4": True})
