"""D-42 permitted characterization (logged before this ran; DEVIATIONS v44).
History-richness of the starved stratum: descriptive comparison of I-1 log_activity =
log(1 + warm_start_positive_count) between the 3,292 starved-at-<=20 controls and the 1,460
clean controls. Covariate-side + label-side ONLY. No indicator, composite, criterion, threshold,
or decision quantity; NO pop_affinity (non-inference clause); nothing from the unsealed payload.

Source: C* covariate cache decompressed b7a0aa36 (25,020-row superset — the only anchored artifact
retaining the starved rows). Strata census-defined (6b6ac55); set-hash asserted before compute or HALT.
Form: median/IQR per stratum; standardized log-scale difference (Cohen's d, starved−clean) with
10,000-iter bootstrap CI seed 201; full ECDFs. Trigger ASSOCIATED iff direction (starved below clean)
AND |d|>=0.2 AND CI excludes 0.
"""
from __future__ import annotations
import gzip, csv, json, hashlib, sys
import numpy as np
sys.path.insert(0, "/Users/david/Dev/loopzero-paper-public/src")
from loopzero_paper.benchmarks.recommender.v2_controls import config as C
from loopzero_paper.benchmarks.recommender.v2_controls.bootstrap import bca_ci

CACHE = C.OUT_DIR / "real_covariates__c-star-25020.csv.gz"
CACHE_SHA = "b7a0aa3615966c82"   # decompressed C* cache prefix (full verified at load)
CENSUS = C.OUT_DIR / "study2_clean_control_census.csv"
OUT = C.OUT_DIR / "s2_exec2_starved_history.json"


def set_hash(ids):
    return hashlib.sha256(",".join(str(u) for u in sorted(ids)).encode()).hexdigest()


def cohens_d(x, y):  # standardized difference x - y, pooled SD
    nx, ny = len(x), len(y)
    sp = np.sqrt(((nx - 1) * x.var(ddof=1) + (ny - 1) * y.var(ddof=1)) / (nx + ny - 2))
    return float((x.mean() - y.mean()) / sp)


def main():
    # census-defined strata
    cen = list(csv.DictReader(open(CENSUS)))
    starved_ids = {int(r["user_id"]) for r in cen if r["is_candidate"] != "1"}
    clean_ids = {int(r["user_id"]) for r in cen if r["is_candidate"] == "1" and r["starved_in_2050"] != "1"}
    assert len(starved_ids) == 3292, f"census starved {len(starved_ids)} != 3292"
    assert len(clean_ids) == 1460, f"census clean {len(clean_ids)} != 1460"

    # C* cache (verify decompressed hash prefix)
    raw = gzip.open(CACHE, "rb").read()
    h = hashlib.sha256(raw).hexdigest()
    assert h.startswith(CACHE_SHA), f"C* cache hash {h[:16]} != anchored {CACHE_SHA}"
    cache = {int(r["user_id"]): float(r["log_activity"]) for r in csv.DictReader(raw.decode().splitlines())}

    # set-hash assertion: every census-stratum user must be present in the C* cache; sets identical
    cache_starved = {u for u in starved_ids if u in cache}
    cache_clean = {u for u in clean_ids if u in cache}
    assert set_hash(cache_starved) == set_hash(starved_ids), "HALT: starved set-hash mismatch vs census"
    assert set_hash(cache_clean) == set_hash(clean_ids), "HALT: clean set-hash mismatch vs census"
    assert len(cache_starved) == 3292 and len(cache_clean) == 1460, "HALT: stratum size mismatch in cache"
    print(f"set-hash assert PASS: starved={len(cache_starved)} clean={len(cache_clean)} (both match census 6b6ac55)", flush=True)

    la_s = np.array([cache[u] for u in sorted(starved_ids)], float)
    la_c = np.array([cache[u] for u in sorted(clean_ids)], float)

    def q(a, p): return float(np.percentile(a, p))
    med_s, med_c = q(la_s, 50), q(la_c, 50)
    iqr_s = [q(la_s, 25), q(la_s, 75)]
    iqr_c = [q(la_c, 25), q(la_c, 75)]

    # standardized difference (starved - clean), 10k bootstrap CI seed 201 (registered lineage)
    pool = np.concatenate([la_s, la_c])
    lab = np.array([1] * len(la_s) + [0] * len(la_c))

    def stat(idx):
        li = lab[idx]; vi = pool[idx]
        s = vi[li == 1]; c = vi[li == 0]
        if len(s) < 2 or len(c) < 2:
            return 0.0
        return cohens_d(s, c)
    d, lo, hi = bca_ci(len(pool), stat, n_boot=10000, seed=201)

    # full ECDF per stratum (log_activity is discrete: log(1+count), count in [0,30])
    def ecdf(a):
        vals = np.sort(np.unique(a))
        return [[round(float(v), 6), round(float((a <= v).mean()), 6)] for v in vals]

    direction_ok = med_s < med_c            # predicted: starved BELOW clean
    mag_ok = abs(d) >= 0.2
    ci_excl0 = (lo > 0) or (hi < 0)
    fired = bool(direction_ok and mag_ok and ci_excl0)

    out = {
        "variable": "log_activity = log(1 + warm_start_positive_count) [WARM-START POSITIVE COUNT — thin early positive history, NOT total volume]",
        "source": "C* covariate cache decompressed b7a0aa36 (25,020-row superset)",
        "strata": {
            "starved_at_<=20": {"n": len(la_s), "median": round(med_s, 6), "IQR": [round(x, 6) for x in iqr_s]},
            "clean": {"n": len(la_c), "median": round(med_c, 6), "IQR": [round(x, 6) for x in iqr_c]},
        },
        "standardized_difference_starved_minus_clean": {
            "cohens_d": round(d, 6), "bootstrap_CI_95": [round(lo, 6), round(hi, 6)],
            "n_boot": 10000, "seed": 201,
        },
        "ecdf_starved": ecdf(la_s),
        "ecdf_clean": ecdf(la_c),
        "trigger_evaluation": {
            "predicted_direction_starved_below_clean": bool(direction_ok),
            "abs_d_ge_0.2": bool(mag_ok),
            "CI_excludes_0": bool(ci_excl0),
            "ASSOCIATED": "FIRED" if fired else "NOT FIRED",
        },
        "licensed_phrase": "users with thin early positive history",
        "non_inference": "pop_affinity deliberately NOT compared (D-42); no taste-popularity inference licensed.",
        "foreclosed_readings": "D-42 (a) and (b) — an association among EXCLUDED units cannot bear on the purified comparison; the starved-sparse stratum is unlabelable by construction (this makes the §11 scope more legible, never smaller).",
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(f"medians: starved={med_s:.4f} (IQR {iqr_s[0]:.4f}-{iqr_s[1]:.4f})  clean={med_c:.4f} (IQR {iqr_c[0]:.4f}-{iqr_c[1]:.4f})", flush=True)
    print(f"cohens_d(starved-clean)={d:.4f} CI[{lo:.4f},{hi:.4f}]", flush=True)
    print(f"trigger: direction={direction_ok} |d|>=0.2={mag_ok} CI_excl0={ci_excl0} -> ASSOCIATED {'FIRED' if fired else 'NOT FIRED'}", flush=True)
    print("STARVED_HISTORY_DONE", flush=True)


if __name__ == "__main__":
    main()
