"""§7 baselines: PC1 (early miss rate) + six v1 EWS families on the step-≤20
miss_run_fraction series.

PC1 is used by the PC1 gate (run now). The six-family scores feed ΔTPR (HELD)
and carry an OPEN DESIGN FLAG (see FAMILY_PARAM_FLAG) that must be confirmed
before any ΔTPR is computed. NOTE-4 (approved): a detector's per-unit score is
its family statistic maxed over the ≤20 window; alarm iff score >= threshold.
"""
from __future__ import annotations
from typing import Sequence
import numpy as np

# --- PC1: fully specified, used by the PC1 gate (run now) ---
def pc1_early_miss_rate(hit: Sequence[int]) -> float:
    """§7 PC1 = (# frontier-miss steps in 1..20) / 20."""
    h = list(hit)
    return sum(1 for x in h if x == 0) / len(h)


# ============================================================================
# OPEN DESIGN FLAG (blocks ΔTPR, not the PC1/PC2 gates):
# §7 says each family is "fully threshold-swept"; §8 says "sweep the threshold".
# The v1 families also carry structural params (window/order/delay/k). Whether
# "best baseline = max over {six families ∪ PC1}" also maximizes over each
# family's v1 param grid, or fixes one canonical param per family, is unspecified.
# The scores below use the maxed-statistic form (NOTE-4) with a single canonical
# param per family; the param policy must be RATIFIED before ΔTPR is run.
FAMILY_PARAM_FLAG = (
    "Unresolved: does 'fully threshold-swept' also sweep each family's structural "
    "param grid (window/order/delay/k), or fix one canonical param? Confirm before ΔTPR."
)
# ============================================================================

def _sliding(series: np.ndarray, w: int):
    if len(series) < w:
        return np.empty((0,))
    return np.lib.stride_tricks.sliding_window_view(series, w)

def variance_ews_score(series: np.ndarray, window: int = 5) -> float:
    win = _sliding(np.asarray(series, float), window)
    return float(win.var(axis=1).max()) if win.size else 0.0

def ac1_score(series: np.ndarray, window: int = 5) -> float:
    s = np.asarray(series, float); win = _sliding(s, window); best = -np.inf
    for w in win:
        w = w - w.mean()
        denom = float(np.dot(w, w))
        best = max(best, float(np.dot(w[:-1], w[1:]) / denom) if denom > 0 else 0.0)
    return best if win.size else 0.0

def cusum_score(series: np.ndarray, k: float = 0.25) -> float:
    s = np.asarray(series, float)
    if len(s) < 2:
        return 0.0
    base = float(s[: min(5, len(s))].mean()); g = 0.0; peak = 0.0
    for x in s:
        g = max(0.0, g + (float(x) - base - k)); peak = max(peak, g)
    return peak

def page_hinkley_score(series: np.ndarray, delta: float = 0.005) -> float:
    s = np.asarray(series, float)
    if len(s) < 2:
        return 0.0
    mean_t = 0.0; ph = 0.0; ph_min = 0.0; peak = 0.0
    for t, x in enumerate(s, start=1):
        x = float(x); mean_t += (x - mean_t) / t; ph += x - mean_t - delta
        ph_min = min(ph_min, ph); peak = max(peak, ph - ph_min)
    return peak

def matrix_profile_score(series: np.ndarray, window: int = 4) -> float:
    s = np.asarray(series, float); n = len(s)
    if n < 2 * window:
        return 0.0
    subs = np.lib.stride_tricks.sliding_window_view(s, window)
    m = len(subs); best = np.full(m, np.inf)
    for i in range(m):
        for j in range(m):
            if abs(i - j) >= window:
                best[i] = min(best[i], float(np.linalg.norm(subs[i] - subs[j])))
    finite = best[np.isfinite(best)]
    return float(finite.max()) if finite.size else 0.0

def permutation_entropy_score(series: np.ndarray, order: int = 3, delay: int = 1) -> float:
    """V-1 fix (conformance, per I-3 'scalarization must be semantically identical
    to the boolean alarm'): the frozen v1 alarm fires on LOW entropy
    (permutation_entropy_alarm: score <= threshold), i.e. permutation entropy is
    DECREASING in alarm propensity. We NEGATE the normalized entropy so that
    'higher score = more alarming' holds throughout (matches v2_prereg_primary
    baseline_score lines 267-268). Ordinal patterns use a STABLE mergesort argsort
    to match the frozen v1 `ordinal_pattern` under ties (the miss series is heavily
    tied). Without this, max-over/≥-threshold scalarization silently inverted PE,
    weakening the best baseline and INFLATING ΔTPR in favour of S."""
    import math
    x = np.asarray(series, dtype=float)
    needed = (order - 1) * delay + 1
    if len(x) < needed + 1:
        return float("nan")
    patterns: dict = {}
    total = 0
    for start in range(0, len(x) - (order - 1) * delay):
        idx = start + np.arange(order) * delay
        pat = tuple(int(i) for i in np.argsort(x[idx], kind="mergesort")[:order])
        patterns[pat] = patterns.get(pat, 0) + 1
        total += 1
    if total == 0:
        return float("nan")
    probs = np.array([c / total for c in patterns.values()], dtype=float)
    entropy = float(-(probs * np.log(probs + 1e-12)).sum())
    max_entropy = math.log(math.factorial(order))
    if max_entropy <= 1e-12:
        return float("nan")
    return -float(entropy / max_entropy)  # NEGATED: higher = more alarming

FAMILY_SCORERS = {
    "variance_ews": variance_ews_score,
    "ac1": ac1_score,
    "cusum": cusum_score,
    "page_hinkley": page_hinkley_score,
    "matrix_profile": matrix_profile_score,
    "permutation_entropy": permutation_entropy_score,
}
