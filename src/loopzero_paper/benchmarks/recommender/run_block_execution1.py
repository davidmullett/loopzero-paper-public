"""Phase 3 BLIND BLOCK — one uninterrupted pass. CP-2 authorized.
No intermediate real-engine number is printed; only {verdict, reason, payload_sha256}
leave the block. The full payload (with decision quantities) is written to a gitignored,
embargoed artifact and hash-anchored — never viewed before the verdict commit.
RATIFIED is set IN-PROCESS (the anchored source stays False; C* unchanged)."""
import sys, time
from pathlib import Path
sys.path.insert(0, "/Users/david/Dev/loopzero-paper-public/src")
from loopzero_paper.benchmarks.recommender.v2_controls import decision as D
from loopzero_paper.benchmarks.recommender.v2_controls import block_orchestrator as BO
from loopzero_paper.benchmarks.recommender.v2_controls import config as C

D.RATIFIED = True   # CP-2 runtime authorization (source unchanged)

CAP = C.REPO / "results/v2_controls/phase25_pre_census.json"
CAP_SHA = "28a73b3aad983b201c275ae159d24e453ed4a069cde79cfd1b616b11d27e3ee9"
OUT = C.OUT_DIR / "s2_verdict_payload.json"

t0 = time.time()
print("[block] START single uninterrupted pass (no intermediate numbers emitted)", flush=True)
real, popularity, shuffled_seeds = BO.compute_summaries()
result = BO.run_block(real, popularity, shuffled_seeds,
                      cap_artifact=CAP, cap_artifact_sha256=CAP_SHA, out_path=OUT)
# information boundary: ONLY these three leave the block
print(f"[block] DONE in {time.time()-t0:.0f}s", flush=True)
print("VERDICT::" + result["verdict"], flush=True)
print("REASON::" + result["reason"], flush=True)
print("PAYLOAD_SHA256::" + result["payload_sha256"], flush=True)
print("BLOCK_DONE", flush=True)
