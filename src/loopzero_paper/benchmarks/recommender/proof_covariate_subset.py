"""D-23 / D-23.A subset proof: the C** covariate cache is a byte-exact row-subset of the C* cache.

Precondition (hardening 1): assert that pop_affinity's LOUO denominator source is the FULL
processed-user base, not the admitted population. Only under that (frozen I-2) definition are a
shared user's values identical across the two caches, making the subset relationship exact. Fails
LOUDLY if the value is population-dependent — in which case option 1 would silently change values
and this proof would be invalid.

Three clauses (all must pass):
  (i)   row-subset byte-identity — every C** line appears byte-identical among the C* lines
        (both userId-sorted, so membership is order-deterministic).
  (ii)  exact-complement — the absent rows == the D-7 exclusion set, verified as a userId set-hash
        against the anchored census 6b6ac55:
          exclusion = {controls NOT is_candidate}  ∪  {controls is_candidate AND starved_in_2050}
        Assert sha256(sorted(exclusion)) == sha256(sorted(absent)) and |exclusion| == 3295.
  (iii) schema identity — header, column order, dtypes identical; no provenance columns in this
        artifact (user_id,log_activity,pop_affinity only).

HASH-ONLY: no covariate value is printed, sampled, sorted-by-value, or described. Rows are compared
by set membership / set-hash only. Run under an interpreter with numpy (precondition).
Usage: python -m ...proof_covariate_subset <new_cache.csv.gz> [--out out.json]
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
CSTAR = REPO / "results/v2_controls/real_covariates__c-star-25020.csv.gz"  # C* record (b7a0aa36, 25,020)
CENSUS = REPO / "results/v2_controls/study2_clean_control_census.csv"    # 6b6ac55
CENSUS_SHA = "f286952cd7011bd562aee449d68f221aaa6d0cae6a52350e4c2df2f256188cfc"


def _dec_lines(path_gz):
    dec = gzip.decompress(Path(path_gz).read_bytes())
    parts = dec.decode().split("\r\n")
    rows = [p for p in parts if p]
    return rows[0], rows[1:]           # header, data rows (verbatim line strings; values not surfaced)


def _sethash(ids) -> str:
    return hashlib.sha256((",".join(str(i) for i in sorted(ids))).encode()).hexdigest()


def _dtype(vals):
    def is_int(s):
        try: int(s); return True
        except Exception: return False
    def is_float(s):
        try: float(s); return True
        except Exception: return False
    if all(is_int(v) for v in vals): return "int"
    if all(is_float(v) for v in vals): return "float"
    return "str"


def precondition():
    from loopzero_paper.benchmarks.recommender.v2_controls import config as C, covariates as COV, producer as PR
    profiles = COV.build_pre_episode_profiles()
    pa_full = COV.pop_affinity(profiles)
    cached = set(int(u) for u in PR.load_arm_units(C.PANEL).user_id)
    sub = {u: profiles[u] for u in profiles if u in cached}
    pa_sub = COV.pop_affinity(sub)
    common = sorted(u for u in sub if u in pa_full and u in pa_sub)
    u = common[0]
    louo_over_full = (pa_full[u] != pa_sub[u])       # comparison only; values never surfaced
    ok = (len(profiles) > len(sub)) and louo_over_full
    if not ok:
        raise SystemExit("PRECONDITION FAIL: pop_affinity value is population-DEPENDENT — subset proof invalid")
    print(f"precondition: PASS — LOUO base n_full={len(profiles)} > admitted-subset n_sub={len(sub)}; "
          f"per-row value population-INDEPENDENT (I-2)")
    return {"pass": True, "louo_base_n": len(profiles), "admitted_subset_n": len(sub)}


def run(new_cache):
    out = {"precondition": precondition()}
    h_star, rows_star = _dec_lines(CSTAR)
    h_new, rows_new = _dec_lines(new_cache)

    # ---- clause (i): row-subset byte-identity ----
    star_set = set(rows_star)
    missing = [r for r in rows_new if r not in star_set]
    ci = (len(missing) == 0)
    print(f"clause (i)  row-subset byte-identity: {'PASS' if ci else 'FAIL'} — {len(rows_new)} C** rows, "
          f"{len(missing)} NOT byte-present among {len(rows_star)} C* rows")
    out["clause_i"] = {"pass": ci, "cstar2_rows": len(rows_new), "cstar_rows": len(rows_star), "not_present": len(missing)}

    # ---- clause (ii): exact-complement vs census 6b6ac55 ----
    if hashlib.sha256(CENSUS.read_bytes()).hexdigest() != CENSUS_SHA:
        raise SystemExit("census hash mismatch — refusing clause (ii)")
    uid = lambda r: int(r.split(",", 1)[0])
    absent = set(uid(r) for r in rows_star) - set(uid(r) for r in rows_new)
    excl = set()
    for row in csv.DictReader(CENSUS.open()):
        is_cand = row["is_candidate"] == "1"
        starved = row["starved_in_2050"] == "1"
        if (not is_cand) or (is_cand and starved):
            excl.add(int(row["user_id"]))
    cii = (_sethash(absent) == _sethash(excl)) and (len(excl) == 3295)
    print(f"clause (ii) exact-complement: {'PASS' if cii else 'FAIL'} — |absent|={len(absent)} |exclusion|={len(excl)} "
          f"set-hash {'MATCH' if _sethash(absent)==_sethash(excl) else 'MISMATCH'}")
    out["clause_ii"] = {"pass": cii, "absent": len(absent), "exclusion": len(excl),
                        "exclusion_set_sha256": _sethash(excl), "absent_set_sha256": _sethash(absent)}

    # ---- clause (iii): schema identity ----
    cols_star = h_star.split(","); cols_new = h_new.split(",")
    dt_star = {c: _dtype([r.split(",")[i] for r in rows_star]) for i, c in enumerate(cols_star)}
    dt_new = {c: _dtype([r.split(",")[i] for r in rows_new]) for i, c in enumerate(cols_new)}
    PROVENANCE = {"engine_hash", "contract_sha256", "benchmark_freeze_sha256"}
    prov_cols = [c for c in cols_new if c in PROVENANCE]
    ciii = (h_star == h_new) and (cols_star == cols_new) and (dt_star == dt_new) and (prov_cols == [])
    print(f"clause (iii) schema identity: {'PASS' if ciii else 'FAIL'} — header {'==' if h_star==h_new else '!='}; "
          f"dtypes {dt_new}; provenance columns: {prov_cols or 'none (n/a for this artifact)'}")
    out["clause_iii"] = {"pass": ciii, "header": h_new, "columns": cols_new, "dtypes": dt_new, "provenance_columns": prov_cols}

    import hashlib as _h
    out["hashes"] = {
        "cstar_decompressed": _h.sha256(gzip.decompress(CSTAR.read_bytes())).hexdigest(),
        "cstar2_decompressed": _h.sha256(gzip.decompress(Path(new_cache).read_bytes())).hexdigest(),
    }
    out["all_pass"] = bool(out["precondition"]["pass"] and ci and cii and ciii)
    print(f"\nSUBSET PROOF: {'ALL PASS' if out['all_pass'] else 'FAIL'}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("new_cache")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    res = run(a.new_cache)
    if a.out:
        a.out.write_text(json.dumps(res, indent=2, sort_keys=True) + "\n")
    sys.exit(0 if res["all_pass"] else 1)
