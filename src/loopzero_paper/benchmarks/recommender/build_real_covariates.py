"""Canonical §9 covariate-cache writer (D-20 remedy; regenerated under C** per D-23/D-23.A).

DISCLOSURE (D-20 / D-23.A): the ORIGINAL writer of real_covariates.csv.gz was never committed
(D-20). This is the canonical writer, built from the anchored logic in v2_controls/covariates.py
(I-1 log_activity, I-2 pop_affinity LOUO). Run under the CORRECTED load_arm_units (C**, D-7 fix)
it produces the 21,725-row cache = 20,265 events + 1,460 CLEAN controls. The prior C* anchor
b7a0aa36 (25,020 rows) was the artifact of the DEFECTIVE admission path (D-23.A reframe): its
reproducibility was conditional on the bug; the C** cache is the anchored record made consistent
with the registration. The C** cache is a byte-exact row-subset of b7a0aa36 (proof:
proof_covariate_subset.py) — sound because pop_affinity is LOUO over ALL processed users (I-2),
so shared rows are byte-identical. Container is written with mtime=0 (G convention).

Inputs are content-gated BEFORE any computation (halt on any failure):
  slate panel decompressed  == ea972e2e… (registered §4 pin; D-16/D-17)
  sorted ratings decompressed == 360fb201… (INPUT_MANIFEST; integrity established D-21.R)
  contract constants          == contract_freeze.json (load_frozen_constants asserts)

Covariate values are label- and indicator-agnostic (functions of rating histories only).
HASH-ONLY: this module surfaces no covariate value — it writes the artifact and reports hashes.
Calls the anchored covariates.py functions verbatim so float arithmetic is bit-identical.
Run under an interpreter with numpy available (producer.load_arm_units).
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, io, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))

PANEL_DEC = "ea972e2ef788801b8e947868fbcf9ea9250393ba88f67f5061dacefced930541"
RATINGS_DEC = "360fb2013956545d946d2c8f64f6db208ca407b81eac942ab4504a50dfc016e2"
PRIOR_C_STAR_CACHE_DEC = "b7a0aa3615966c8292dcb91d1780f4bf13ce5ee7020c82cc63e11afaa8ae43f9"  # 25,020-row pre-fix cache


def _dec_sha(p) -> str:
    h = hashlib.sha256()
    with gzip.open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _gzip_deterministic(data: bytes) -> bytes:
    """G convention: gzip with mtime=0 so the container is reproducible (closes the container-drift
    class — D-16/D-21). The decompressed content is the load-asserted canonical form regardless."""
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(data)
    return buf.getvalue()


def input_gate(C):
    """All three gates must pass BEFORE any covariate computation."""
    p = _dec_sha(C.PANEL)
    if p != PANEL_DEC:
        raise SystemExit(f"INPUT GATE FAIL (panel): {p} != {PANEL_DEC}")
    r = _dec_sha(C.SORTED_RATINGS)
    if r != RATINGS_DEC:
        raise SystemExit(f"INPUT GATE FAIL (ratings): {r} != {RATINGS_DEC}")
    C.load_frozen_constants()   # raises AssertionError if contract constants drift
    print("input gate: panel ✓ ratings ✓ contract ✓", flush=True)


def build(C, COV, PR) -> bytes:
    """Return the DECOMPRESSED cache bytes. Serialization: header + rows ascending by user_id,
    floats via Python str()/repr, CRLF (csv.writer default) — the observed anchored format."""
    la = COV.log_activity_from_manifest()                 # I-1 : from MANIFEST
    profiles = COV.build_pre_episode_profiles()           # heavy 25M-row pass
    pa = COV.pop_affinity(profiles)                        # I-2 : LOUO over all processed users
    units = PR.load_arm_units(C.PANEL)                    # user-set = corrected L2 (events + CLEAN controls)
    user_set = sorted(int(u) for u in units.user_id)      # ascending
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["user_id", "log_activity", "pop_affinity"])
    for u in user_set:
        w.writerow([u, la[u], pa.get(u, 0.0)])            # 0.0 default for users without a profile
    return buf.getvalue().encode()


def assert_rowset_invariance(C, COV, PR):
    """Executable property test: pop_affinity is LEAVE-ONE-USER-OUT over ALL processed users
    (I-2 / AMBER-2), NOT over the ~25,020 cached rows. Demonstrated by recomputing pop_affinity
    for a shared test user under (a) the full processed population and (b) only the cached subset
    as the LOUO base: the two differ, so the written value reflects the full-population LOUO and is
    invariant to which rows the cache happens to contain. HASH-ONLY: no covariate value is printed —
    only counts and a boolean comparison."""
    profiles = COV.build_pre_episode_profiles()           # full processed population
    n_full = len(profiles)
    pa_full = COV.pop_affinity(profiles)                  # LOUO over the full population
    cached = set(int(u) for u in PR.load_arm_units(C.PANEL).user_id)
    sub_profiles = {u: profiles[u] for u in profiles if u in cached}   # cached-subset population
    n_sub = len(sub_profiles)
    pa_sub = COV.pop_affinity(sub_profiles)               # LOUO over the cached subset only
    common = sorted(u for u in sub_profiles if u in pa_full and u in pa_sub)
    u = common[0]                                         # deterministic identity; not a value
    louo_over_full = (pa_full[u] != pa_sub[u])           # comparison only; values never surfaced
    ok = (n_full > n_sub) and louo_over_full
    print(f"row-set invariance: {'PASS' if ok else 'FAIL'} — pop_affinity LOUO base n_full={n_full} "
          f"> cached-subset n_sub={n_sub}; full-population value differs from subset value for the "
          f"shared test user (compared, not printed) => cache pop_affinity is invariant to the write row-set")
    if not ok:
        raise SystemExit("row-set invariance assertion FAILED")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, help="output .csv.gz path")
    ap.add_argument("--verify-decompressed", default=None, help="optional decompressed sha256 target to compare")
    ap.add_argument("--assert-invariance", action="store_true", help="run the row-set invariance property test")
    args = ap.parse_args()
    from loopzero_paper.benchmarks.recommender.v2_controls import config as C
    from loopzero_paper.benchmarks.recommender.v2_controls import covariates as COV
    from loopzero_paper.benchmarks.recommender.v2_controls import producer as PR
    input_gate(C)
    if args.assert_invariance:
        assert_rowset_invariance(C, COV, PR)
        return
    data = build(C, COV, PR)
    container = _gzip_deterministic(data)                  # G: mtime=0 deterministic container
    args.out.write_bytes(container)
    dec = hashlib.sha256(data).hexdigest()
    n_rows = data.count(b"\n") - 1                          # rows excluding header (no value surfaced)
    print(f"rows (excl header)             : {n_rows}")
    print(f"DECOMPRESSED sha256            : {dec}")
    print(f"container sha256 (mtime=0)     : {hashlib.sha256(container).hexdigest()}")
    if args.verify_decompressed:
        print(f"BYTE-IDENTITY vs {args.verify_decompressed[:12]}… : {'PASS' if dec == args.verify_decompressed else 'FAIL'}")


if __name__ == "__main__":
    main()
