"""RULING 9 — config ⇄ wka72 registration conformance test.

Asserts that each config.py constant equals the frozen wka72 register value in
`wka72_registration_params.json` (clause-referenced extract).

EXPECTED STATE (pre-C**): this test is EXPECTED TO FAIL on the budget grid — config.py
still carries the Study-1 grid {0.01,0.02,0.05,0.10} while wka72 registers {0.02,0.05,0.10,0.20}
(DEVIATIONS D-15). The failure DEMONSTRATES THE TEST WORKS; it is the guard that will make the
budget-grid nonconformance impossible to miss at C**. Do not "fix" the test — fix config at C**.

Embargoed (reads embargoed config.py + extract); hash-anchored via REGISTRATION_PARAMS.sha256.
config.py imports only json+pathlib (numpy-free), so this runs without the analysis deps.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[2]
CONFIG_DIR = REPO / "src/loopzero_paper/benchmarks/recommender/v2_controls"
EXTRACT = HERE.with_name("wka72_registration_params.json")


def _norm(v):
    return list(v) if isinstance(v, (list, tuple)) else v


def run():
    sys.path.insert(0, str(CONFIG_DIR))
    import config as C  # numpy-free import
    reg = json.loads(EXTRACT.read_text())
    params, cmap = reg["params"], reg["config_equality_map"]
    results, failures = [], []
    for attr, key in cmap.items():
        if attr.startswith("_"):
            continue
        code_val = _norm(getattr(C, attr))
        reg_val = _norm(params[key]["value"])
        ok = code_val == reg_val
        results.append((attr, key, code_val, reg_val, ok, params[key]["clause"]))
        if not ok:
            failures.append((attr, key, code_val, reg_val, params[key]["clause"]))
    print(f"config ⇄ wka72 conformance: {len(results)-len(failures)}/{len(results)} pass")
    for attr, key, cv, rv, ok, cl in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] config.{attr} = {cv}  vs wka72.{key} = {rv}  ({cl})")
    return failures


def assert_q5_budget_closure():
    """Q5 class closure: EVERY budget referenced by any gate or I-entry must resolve to a
    registered-grid value, so future grid drift breaks THE BUILD rather than the registration.
    Covers: config.BUDGETS / decision.BUDGETS (criteria 1&2), config/decision.PRIMARY_BUDGET
    (I-7 PC1 learnability gate + all gate operating points)."""
    sys.path.insert(0, str(REPO / "src"))
    from loopzero_paper.benchmarks.recommender.v2_controls import config as C
    from loopzero_paper.benchmarks.recommender.v2_controls import decision as D
    reg = json.loads(EXTRACT.read_text())
    grid = tuple(reg["params"]["budgets"]["value"])
    primary = reg["params"]["primary_budget"]["value"]
    referenced = set(C.BUDGETS) | set(D.BUDGETS) | {C.PRIMARY_BUDGET, D.PRIMARY_BUDGET}
    problems = []
    if not referenced <= set(grid):
        problems.append(f"budgets referenced outside registered grid: {sorted(referenced - set(grid))}")
    if tuple(C.BUDGETS) != grid:
        problems.append(f"config.BUDGETS {tuple(C.BUDGETS)} != registered grid {grid}")
    if tuple(D.BUDGETS) != grid:
        problems.append(f"decision.BUDGETS {tuple(D.BUDGETS)} != registered grid {grid}")
    if C.PRIMARY_BUDGET != primary or D.PRIMARY_BUDGET != primary:
        problems.append(f"PRIMARY_BUDGET != registered {primary} (config={C.PRIMARY_BUDGET}, decision={D.PRIMARY_BUDGET})")
    if problems:
        for p in problems:
            print("  Q5 FAIL:", p)
        raise SystemExit("Q5 budget-closure assertion FAILED")
    print(f"Q5 budget closure: PASS — referenced budgets {sorted(referenced)} ⊆ registered grid "
          f"{sorted(grid)}; config.BUDGETS == decision.BUDGETS == grid; primary == {primary} "
          f"(I-7 / gates operate here)")


if __name__ == "__main__":
    failures = run()
    assert_q5_budget_closure()
    if failures:
        print(f"\n{len(failures)} DIVERGENCE(S):")
        for attr, key, cv, rv, cl in failures:
            print(f"  config.{attr} {cv} != wka72 {rv} ({cl})")
        sys.exit(1)
    print("\nAll config constants conform to wka72; Q5 budget closure holds.")
    sys.exit(0)
