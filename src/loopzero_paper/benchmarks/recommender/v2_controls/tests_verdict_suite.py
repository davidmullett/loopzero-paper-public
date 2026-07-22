"""Known-answer verdict test suite + label-permuted synthetic debug (Phase 1, step 4/5).

Part A: decision.verdict on synthetic KNOWN-ANSWER cases — every assert must pass.
Part B: exercise the sweep / BCa / covariate machinery on label-permuted synthetic
populations (chance by construction) — ΔTPR ~ 0 and incremental AUC ~ 0 with CIs
that include 0. No real-engine indicator×label quantity. decision.RATIFIED stays False.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "src"))
from loopzero_paper.benchmarks.recommender.v2_controls import decision as D
from loopzero_paper.benchmarks.recommender.v2_controls import sweep as SW
from loopzero_paper.benchmarks.recommender.v2_controls import covariate_model as CM
from loopzero_paper.benchmarks.recommender.v2_controls.bootstrap import bca_ci
from loopzero_paper.benchmarks.recommender.v2_controls import config as C

BUD = D.BUDGETS

# ---------- builders ----------
def real(**over):
    base = dict(eval_events=10153, pc1_minus_b=(0.20, 0.10, 0.30), pc2_pass=True,
                delta_by_budget={b: (0.08, 0.03, 0.13) for b in BUD},   # c1 met, c2 met (all +)
                cov_bG=(0.5, 0.2, 0.8), cov_bP=(0.4, 0.1, 0.7),
                cov_bD=(-0.5, -0.8, -0.2), cov_incr_auc=(0.05, 0.02, 0.08))  # c3 met
    base.update(over)
    return D.RealArm(**base)

UNMET = (0.00, -0.02, 0.02)    # crit-1 bar NOT met (point<0.05, CI includes 0) — good severed arm
MET   = (0.09, 0.04, 0.14)     # crit-1 bar MET (S separates on the severed arm) — blocks SURVIVES

def ctrl(name, delta, measurable=True):
    if measurable:
        return D.ControlArm(name, n_clean_controls=800, n_events=5000, s_distinct=42, s_iqr=0.03, delta_b05=delta)
    return D.ControlArm(name, n_clean_controls=50, n_events=80, s_distinct=8, s_iqr=0.0, delta_b05=delta)

def seeds(pattern):  # pattern: list of 5 CIs
    return [ctrl(f"shuffledTS_10{2+i}", pattern[i]) for i in range(5)]

# ---------- Part A: known-answer cases ----------
cases = []
def check(name, got, expect):
    ok = (got["verdict"] == expect)
    cases.append({"case": name, "expected": expect, "got": got["verdict"], "reason": got["reason"], "pass": ok})
    return ok

# (a) recursion-severed artifact: S separates on shuffled-TS seeds -> SURVIVES BLOCKED (DIES via crit4)
check("a_artifact_recursion_severed_S_separates",
      D.verdict(real(), ctrl("popularity", UNMET), seeds([UNMET, MET, UNMET, MET, UNMET])),
      "SIGNAL DIES")
# (b) dispositive (popularity) arm below I-5a floor -> UNINTERPRETABLE-BY-CONTROL-ARM
check("b_dispositive_unmeasurable",
      D.verdict(real(), ctrl("popularity", UNMET, measurable=False), seeds([UNMET]*5)),
      "UNINTERPRETABLE-BY-CONTROL-ARM")
# (b2) one shuffled-TS seed unmeasurable -> UNINTERPRETABLE-BY-CONTROL-ARM (I-8)
_seeds = seeds([UNMET]*5); _seeds[3] = ctrl("shuffledTS_105", UNMET, measurable=False)
check("b2_one_shuffled_seed_unmeasurable",
      D.verdict(real(), ctrl("popularity", UNMET), _seeds),
      "UNINTERPRETABLE-BY-CONTROL-ARM")
# (c) exactly one of five shuffled-TS seeds retains S's advantage -> SURVIVES BLOCKED (DIES; I-8 unanimity)
check("c_one_of_five_seeds_retains",
      D.verdict(real(), ctrl("popularity", UNMET), seeds([UNMET, UNMET, UNMET, MET, UNMET])),
      "SIGNAL DIES")
# (d1) clean four-criteria pass -> SURVIVES
check("d1_clean_pass",
      D.verdict(real(), ctrl("popularity", UNMET), seeds([UNMET]*5)),
      "SIGNAL SURVIVES")
# (d2) clear miss on criterion 1 -> DIES
check("d2_clear_miss",
      D.verdict(real(delta_by_budget={**{b:(0.08,0.03,0.13) for b in BUD}, 0.05:(0.01,-0.01,0.03)}),
                ctrl("popularity", UNMET), seeds([UNMET]*5)),
      "SIGNAL DIES")
# (a2) PRECEDENCE: criteria 1-3 FAIL and a dispositive arm is UNMEASURABLE -> DIES.
# criteria 1-3 are evaluated first; a real-engine null cannot hide behind UNINTERPRETABLE.
check("a2_criteria_fail_and_dispositive_unmeasurable",
      D.verdict(real(delta_by_budget={**{b:(0.08,0.03,0.13) for b in BUD}, 0.05:(0.01,-0.01,0.03)}),
                ctrl("popularity", UNMET, measurable=False), seeds([UNMET]*5)),
      "SIGNAL DIES")
# (e) PC1 at chance -> UNINTERPRETABLE-BY-CONSTRUCTION (I-7 / D-2)
check("e_pc1_at_chance",
      D.verdict(real(pc1_minus_b=(0.0, -0.05, 0.05)), ctrl("popularity", UNMET), seeds([UNMET]*5)),
      "UNINTERPRETABLE-BY-CONSTRUCTION")
# (f) power gate -> INDETERMINATE-BY-POWER
check("f_power_gate",
      D.verdict(real(eval_events=150), ctrl("popularity", UNMET), seeds([UNMET]*5)),
      "INDETERMINATE-BY-POWER")
# (g) PC2 fail -> UNINTERPRETABLE-BY-CONSTRUCTION
check("g_pc2_fail",
      D.verdict(real(pc2_pass=False), ctrl("popularity", UNMET), seeds([UNMET]*5)),
      "UNINTERPRETABLE-BY-CONSTRUCTION")
# (h) popularity retains advantage (personalization-severed) -> DIES
check("h_popularity_retains",
      D.verdict(real(), ctrl("popularity", MET), seeds([UNMET]*5)),
      "SIGNAL DIES")
# (12) C4 DOMINANCE mixed case: criteria 1-3 hold; popularity MEASURABLE + RETAINS (bar met);
# one shuffled-TS seed UNMEASURABLE -> DIES. Measurable retention (criterion 4 failed) dominates
# unmeasurability; must NOT return UNINTERPRETABLE-BY-CONTROL-ARM (ratified 2026-07-17).
_mixed_seeds = seeds([UNMET] * 5); _mixed_seeds[3] = ctrl("shuffledTS_105", UNMET, measurable=False)
check("i_c4_dominance_measurable_retention_over_unmeasurable_seed",
      D.verdict(real(), ctrl("popularity", MET), _mixed_seeds),
      "SIGNAL DIES")

all_A_pass = all(c["pass"] for c in cases)

# ---------- Part B: label-permuted synthetic debug of sweep / BCa / covariate ----------
rng = np.random.default_rng(20260717)
n = 2000
user_id = np.arange(1, n + 1)
S_score = rng.normal(size=n)
base1 = rng.normal(size=n); base2 = rng.normal(size=n)          # two synthetic baseline detectors
cov = rng.normal(size=(n, 2))                                    # log_activity, pop_affinity
ind = rng.normal(size=(n, 3))                                    # z(G), z(p), z(δ)
# permuted labels: event with prevalence ~0.8, INDEPENDENT of all features (chance by construction)
y = (rng.random(n) < 0.8).astype(int)

def matched_count(is_event):
    nc = int((~is_event).sum())
    return SW.matched_count(0.05, nc)

def delta_tpr_stat(idx):
    ie = y[idx].astype(bool)
    cnt = matched_count(ie)
    tpr_s = SW.matched_tpr(S_score[idx], ie, user_id[idx], cnt)
    # I-6: best baseline re-maxed WITHIN this replicate
    tpr_b = max(SW.matched_tpr(base1[idx], ie, user_id[idx], cnt),
                SW.matched_tpr(base2[idx], ie, user_id[idx], cnt))
    return tpr_s - tpr_b

dt_pt, dt_lo, dt_hi = bca_ci(n, delta_tpr_stat, n_boot=1000, seed=C.BOOTSTRAP_SEED)

def incr_auc_stat(idx):
    return CM.incremental_auc(cov[idx], ind[idx], y[idx])

ia_pt, ia_lo, ia_hi = bca_ci(n, incr_auc_stat, n_boot=400, seed=C.BOOTSTRAP_SEED)

# chance expectations: point near 0, CI includes 0
partB = {
    "delta_tpr_permuted": {"point": round(dt_pt, 4), "ci": [round(dt_lo, 4), round(dt_hi, 4)],
                           "ci_includes_0": bool(dt_lo <= 0 <= dt_hi), "near_zero": bool(abs(dt_pt) < 0.15)},
    "incremental_auc_permuted": {"point": round(ia_pt, 4), "ci": [round(ia_lo, 4), round(ia_hi, 4)],
                                 "ci_includes_0": bool(ia_lo <= 0 <= ia_hi), "near_zero": bool(abs(ia_pt) < 0.10)},
}
partB_ok = (partB["delta_tpr_permuted"]["ci_includes_0"] and partB["delta_tpr_permuted"]["near_zero"]
            and partB["incremental_auc_permuted"]["ci_includes_0"] and partB["incremental_auc_permuted"]["near_zero"])

result = {
    "stage": "verdict_test_suite", "decision_RATIFIED": D.RATIFIED,
    "partA_known_answer_cases": cases, "partA_all_pass": all_A_pass,
    "partB_label_permuted_debug": partB, "partB_chance_confirmed": partB_ok,
    "all_pass": bool(all_A_pass and partB_ok),
}
out = C.OUT_DIR / "verdict_test_suite_results.json"
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
for c in cases:
    print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {c['case']:42s} -> {c['got']}")
print(f"\nPart A all pass: {all_A_pass}")
print(f"Part B (chance): ΔTPR={partB['delta_tpr_permuted']}  incrAUC={partB['incremental_auc_permuted']}")
print(f"Part B chance confirmed: {partB_ok}")
print(f"ALL PASS: {result['all_pass']}")
if not result["all_pass"]:
    sys.exit(1)
