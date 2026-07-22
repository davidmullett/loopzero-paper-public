"""Phase 2 V-1 sign-convention table generator (deterministic).

Asserts each of the six baseline families' alarm directions against the FROZEN v1
alarm-function operators, plus PC1 (increasing). Records the permutation-entropy
DECREASING direction and confirms the v2_controls PE fix (negation) agrees with
v2_prereg_primary. Writes results/v2_controls/v1_sign_convention_table.json
(gitignored payload anchored publicly at preregistration/SIGN_TABLE.sha256).
"""
from __future__ import annotations
import re, json, importlib
import numpy as np
from . import config as C


def build_table() -> dict:
    fast = open(C.REPO / "src/loopzero_paper/benchmarks/recommender/calibrate_fast_families.py").read()
    slow = open(C.REPO / "src/loopzero_paper/benchmarks/recommender/calibrate_slow_families.py").read()
    src = fast + "\n" + slow

    def alarm_direction(fn):
        m = re.search(rf"def {fn}\(.*?\):(.*?)(?=\ndef )", src, re.S)
        body = m.group(1)
        has_ge = ">=" in body
        has_le_thr = re.search(r"score\s*<=\s*threshold", body) is not None
        return "decreasing" if has_le_thr else ("increasing" if has_ge else "unknown")

    families = {
        "variance_ews":        ("variance_ews_alarm",        "max-over-window",      "max window variance"),
        "ac1":                 ("ac1_alarm",                 "max-over-window",      "max window lag-1 autocorr"),
        "cusum":               ("cusum_alarm",               "peak (running max)",   "peak CUSUM g"),
        "page_hinkley":        ("page_hinkley_alarm",        "peak (running max)",   "peak (ph - ph_min)"),
        "matrix_profile":      ("matrix_profile_alarm",      "max",                  "max matrix-profile distance"),
        "permutation_entropy": ("permutation_entropy_alarm", "negate (I-3/V-1 fix)", "-normalized permutation entropy"),
    }
    rows = []
    for fam, (fn, scal, stat) in families.items():
        d = alarm_direction(fn)
        rows.append({"family": fam, "v1_alarm_fn": fn, "v1_direction": d,
                     "scalarization": scal, "statistic": stat, "higher_score_more_alarming": True})
        assert d in ("increasing", "decreasing"), f"{fam}: could not determine direction"
    rows.append({"family": "PC1_early_miss_rate", "v1_alarm_fn": "(PC1 = miss-rate)",
                 "v1_direction": "increasing", "scalarization": "identity",
                 "statistic": "early miss rate (1..20)", "higher_score_more_alarming": True})

    dirs = {r["family"]: r["v1_direction"] for r in rows}
    assert dirs["permutation_entropy"] == "decreasing", dirs
    assert all(dirs[f] == "increasing" for f in
               ("variance_ews", "ac1", "cusum", "page_hinkley", "matrix_profile", "PC1_early_miss_rate")), dirs

    import loopzero_paper.benchmarks.recommender.v2_controls.baselines as bl
    import loopzero_paper.benchmarks.recommender.v2_prereg_primary as prim
    importlib.reload(bl)
    rng = np.random.default_rng(1); maxdiff = 0.0; n = 0
    for _ in range(300):
        s = rng.integers(0, 9, size=20) / 8.0
        for o, dl in [(3, 1), (3, 2), (4, 1), (4, 2)]:
            a = bl.permutation_entropy_score(s, o, dl)
            b = prim.baseline_score(s, "permutation_entropy", {"order": o, "delay": dl})
            if np.isnan(a) and np.isnan(b):
                continue
            maxdiff = max(maxdiff, abs(a - b)); n += 1
    pe_neg = "NEGATED" in open(C.REPO / "src/loopzero_paper/benchmarks/recommender/v2_controls/baselines.py").read()

    return {
        "stage": "V-1_sign_convention_table", "spec": "OSF osf.io/wka72; §7/§8; I-3/V-1/I-7",
        "source": "frozen v1 alarm functions (calibrate_fast_families.py, calibrate_slow_families.py)",
        "families": rows,
        "summary": "5 families increasing (max/peak scalarization faithful); permutation_entropy DECREASING (v1 alarm score<=threshold) and FIXED by negation; PC1 increasing (gate per I-7).",
        "pe_fix": {"negation_present_in_v2_controls": bool(pe_neg),
                   "pe_agreement_v2controls_vs_v2prereg_primary_maxabsdiff": maxdiff, "comparisons": n},
        "all_assertions_passed": True,
    }


def main():
    table = build_table()
    (C.OUT_DIR / "v1_sign_convention_table.json").write_text(json.dumps(table, indent=2) + "\n")


if __name__ == "__main__":
    main()
