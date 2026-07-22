"""Phase-2a runner: §4 population accounting + WHOLE-L diagnostics (PC1/PC2/power gates + a
matched-count table).

RELABEL (D-27): every gate and matched-count quantity here is a §4 WHOLE-L DIAGNOSTIC computed
over ALL controls — it is NOT the registered §5/§6 operating point. The registered PC1/PC2 gates
and §6 matched counts are computed ONLY in the block (producer.py / block_orchestrator.py) over
the CLEAN population. The PC1 TPR here is the Study-1 pathology quantity published as D-2. These
diagnostics carry the §4 grid {0.01,0.02,0.05,0.10}, not the §6 grid — they are not bound to it.

Runs ONLY non-decision quantities (authorized). Imports decision.py but never calls it. Writes
results/v2_controls/phase2a_accounting_and_gates.json. NOT re-run under C*** (the on-disk file is
the published D-2 record; the relabel is code-only).
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "src"))
from loopzero_paper.benchmarks.recommender.v2_controls import config as C
from loopzero_paper.benchmarks.recommender.v2_controls import population as P
from loopzero_paper.benchmarks.recommender.v2_controls import gates as G

# D-27 / ruling 4: the §4 whole-L diagnostic k table is NOT bound to the registered §6 grid.
# Decoupled from C.BUDGETS on purpose — referencing the §6 grid constant is part of the
# "dressed as §6" defect this relabel closes.
S4_WHOLEL_DIAGNOSTIC_GRID = (0.01, 0.02, 0.05, 0.10)


def main() -> dict:
    t0 = time.time()
    assert os.environ.get("PYTHONHASHSEED") == "0", "§13: pin PYTHONHASHSEED=0 before running"
    frozen = C.load_frozen_constants()
    print(f"[load] frozen constants engine_hash={frozen['engine_hash']}", flush=True)

    units = P.load_units()
    L = P.landmark_L(units)
    print(f"[load] units={len(units):,}  L={len(L):,}  ({time.time()-t0:.0f}s)", flush=True)

    accounting = P.population_accounting(units)
    power = G.power_gate(accounting["eval_events_in_L"])
    print("[gate] power:", power["verdict"], flush=True)

    pc2 = G.pc2_gate(L)
    print(f"[gate] PC2 δ-liveness: pass={pc2['pass']} distinct={pc2['n_distinct_delta_values_over_L']} IQR={pc2['delta_IQR']:.4f}", flush=True)

    print("[gate] PC1 learnability (BCa 10k, seed 201) — running...", flush=True)
    pc1 = G.pc1_gate(L)
    print(f"[gate] PC1 TPR@0.05={pc1['PC1_TPR_at_b05']} CI={pc1['PC1_TPR_BCa95']}", flush=True)

    report = {
        "stage": "phase2a_accounting_and_gates",
        "scope": "NON-DECISION ONLY; §11 ΔTPR/AUC/four-criteria HELD pending author ratification",
        "engine_hash": frozen["engine_hash"],
        "contract_sha256": frozen["contract_sha256"],
        "panel_md5_expected": "d486f59c97701c177e16c8eb0bde4a11",
        "deviations_applied": C.DEVIATIONS,
        "population_accounting_s4": accounting,
        "power_gate_s11": power,
        "pc2_gate_liveness": pc2,
        "pc1_gate_learnability": pc1,
        # D-27 relabel: §4 WHOLE-L diagnostic counts (all controls), §4 grid — NOT §6 operating points.
        "s4_wholeL_diagnostic_counts": {
            str(b): int(round(b * accounting["eval_controls_in_L"])) for b in S4_WHOLEL_DIAGNOSTIC_GRID
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    out = C.OUT_DIR / "phase2a_accounting_and_gates.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"[ok] wrote {out}", flush=True)
    return report


if __name__ == "__main__":
    main()
