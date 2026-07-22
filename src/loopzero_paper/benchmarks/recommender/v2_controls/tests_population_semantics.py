"""Population-semantics conformance (C***, D-27 / ruling 3). Two assertions, both break the build.

(B) PRIMARY — the clearance guard. No site OUTSIDE the block computes a clean-population gate or
    indicator×label quantity. Structural: the block (producer.py, block_orchestrator.py) is the only
    place permitted to pair an indicator / PC series with is_event through `matched_tpr` over a
    CLEAN-restricted population; gates.py and run_phase2a.py must remain whole-L. Enforced by the
    fact that the §4 path (population.Unit) has no clean concept, plus a source check that no
    non-block matched_tpr caller references clean. FAILURE OF (B) WOULD VOID THE CONTAMINATION
    CLEARANCE — category (b) must stay empty.

(A) SECONDARY — §6-denominator conformance, scoped to the block + pre_census ONLY: their §6
    matched-count / z-source / measurability quantities use the CLEAN denominator. Deliberately NOT
    applied to gates.py / run_phase2a.py — after the D-27 relabel those are whole-L §4 diagnostics
    and no longer claim §6; applying (A) there would wrongly flag a legitimate whole-L diagnostic.

KNOWN BOUND (honest, not closed): both catch regressions at enumerated / structurally-scanned sites.
A newly-added, UNREGISTERED site that computed a clean gate outside the block would not be caught
until registered. (B) in structural form is more resistant than (A) because the §4 path lacks a clean
concept, but neither is a solved problem — this is a bound, not a proof.
"""
from __future__ import annotations
import sys
from pathlib import Path

V2 = Path(__file__).resolve().parent
GATE_OP = "matched_tpr"                       # the indicator×label gate operator (sweep.py defines it)
CLEAN_TOKENS = ("clean_control", "clean_controls", "study2_clean_control_census")
BLOCK = {"producer.py", "block_orchestrator.py"}
NON_SOURCE = {"sweep.py"}                      # defines matched_tpr; not a caller site
WHOLE_L_DIAGNOSTIC = ("gates.py", "run_phase2a.py")


def _src(name: str) -> str:
    return (V2 / name).read_text()


def assert_B_no_clean_gate_outside_block():
    problems = []
    # every non-test module that CALLS the gate operator
    callers = sorted(p.name for p in V2.glob("*.py")
                     if p.name not in NON_SOURCE and not p.name.startswith("tests_")
                     and (GATE_OP + "(") in _src(p.name))
    for name in callers:
        if name in BLOCK:
            continue
        if any(tok in _src(name) for tok in CLEAN_TOKENS):
            problems.append(f"{name} calls {GATE_OP} AND references clean -> clean-population gate OUTSIDE the block")
    # the whole-L §4 diagnostics must not reference clean at all
    for name in WHOLE_L_DIAGNOSTIC:
        if any(tok in _src(name) for tok in CLEAN_TOKENS):
            problems.append(f"{name} references clean -> §4 diagnostic drifted to clean population (category-b risk)")
    ok = not problems
    print(f"(B) no clean gate outside block: {'PASS' if ok else 'FAIL'} — gate-operator callers {callers}; "
          f"block={sorted(BLOCK & set(callers))}; whole-L diagnostics clean-free")
    for p in problems:
        print("   (B) FAIL:", p)
    return ok


def assert_A_sixsix_denominator_clean():
    """Scoped to the §6-claiming sites: block (producer) + pre_census. Token-level structural check."""
    problems = []
    prod = _src("producer.py")
    # load_arm_units admits control iff CLEAN (site 84); z-source & measurability on clean_control
    if 'lab == "control" and not rec["starved"]' not in prod:
        problems.append("producer.load_arm_units in_L2 does not admit control-and-CLEAN only")
    if '(a.fold == "cal") & a.clean_control' not in prod:
        problems.append("producer.s_scores z-source not on cal-fold CLEAN controls")
    if "ev & a.clean_control" not in prod and "(ev & a.clean_control)" not in prod:
        problems.append("producer.measurability n_clean not on clean_control")
    # pre_census §6 matched k over CLEAN (D-26)
    if 'ev["clean_controls"]' not in _src("pre_census.py"):
        problems.append("pre_census k table not over eval CLEAN controls (D-26)")
    ok = not problems
    print(f"(A) §6-denominator clean at block + pre_census: {'PASS' if ok else 'FAIL'}")
    for p in problems:
        print("   (A) FAIL:", p)
    return ok


def run():
    b = assert_B_no_clean_gate_outside_block()
    a = assert_A_sixsix_denominator_clean()
    print("\nKNOWN BOUND: catches regressions at enumerated/scanned sites; a new unregistered clean-gate "
          "site outside the block is not auto-caught until registered. (B) structural > (A); neither is closed.")
    return b and a


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
