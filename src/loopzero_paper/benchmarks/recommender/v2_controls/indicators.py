"""§6 redefined indicators — PURE functions of the ranked slates {R_1..R_20}.

Computed from slate_json ONLY (never the legacy G/p/delta columns), per §6
"formulas govern". Formulas transcribed verbatim from the frozen doc §6.
"""
from __future__ import annotations
from typing import List, Sequence, Tuple
import numpy as np
from . import config as C


def churn_G(slates: Sequence[Sequence[int]]) -> float:
    """§6 G: c_t = 1 - |R_t ∩ R_{t+1}| / |R_t ∪ R_{t+1}|, t=1..19; G_u = mean(c_t)."""
    cs = []
    for t in range(len(slates) - 1):
        a = set(slates[t]); b = set(slates[t + 1])
        union = a | b
        c = 1.0 - (len(a & b) / len(union)) if union else 0.0
        cs.append(c)
    return float(np.mean(cs)) if cs else 0.0


def coverage_delta(slates: Sequence[Sequence[int]]) -> float:
    """§6 δ: |∪_{t=1..20} R_t| / 200."""
    seen = set()
    for r in slates:
        seen.update(r)
    return len(seen) / C.N_SLOTS


def occupancy_p(slates: Sequence[Sequence[int]]) -> float:
    """§6 p: n_i=#{t: i∈R_t}; s_i=n_i/200; p_u = Σ_i s_i² (Herfindahl over 200 slots)."""
    from collections import Counter
    occ = Counter()
    for r in slates:
        occ.update(r)
    return float(sum((n / C.N_SLOTS) ** 2 for n in occ.values()))


def churn_slope_G(slates: Sequence[Sequence[int]]) -> float:
    """§6 descriptive secondary: OLS slope of c_t on t."""
    cs = []
    for t in range(len(slates) - 1):
        a = set(slates[t]); b = set(slates[t + 1]); union = a | b
        cs.append(1.0 - (len(a & b) / len(union)) if union else 0.0)
    if len(cs) < 2:
        return 0.0
    t = np.arange(1, len(cs) + 1, dtype=float)
    y = np.asarray(cs, dtype=float)
    return float(np.polyfit(t, y, 1)[0])


def all_indicators(slates: Sequence[Sequence[int]]) -> Tuple[float, float, float]:
    return churn_G(slates), occupancy_p(slates), coverage_delta(slates)


class ZParams:
    """§6: z-parameters (mean, SD) estimated on CALIBRATION-FOLD CONTROLS in L.

    SD uses sample standard deviation (ddof=1) — disclosed implementation choice
    (spec says 'mean, SD'; ddof unspecified). Only affects the composite S, which
    is a HELD decision quantity, not the PC1/PC2 gates.
    """
    def __init__(self, g: np.ndarray, p: np.ndarray, d: np.ndarray):
        self.mu = {"G": float(np.mean(g)), "p": float(np.mean(p)), "delta": float(np.mean(d))}
        self.sd = {"G": float(np.std(g, ddof=1)), "p": float(np.std(p, ddof=1)), "delta": float(np.std(d, ddof=1))}

    def z(self, name: str, x: np.ndarray) -> np.ndarray:
        sd = self.sd[name]
        return (np.asarray(x, float) - self.mu[name]) / sd if sd > 0 else np.zeros_like(np.asarray(x, float))


def composite_S(zG: np.ndarray, zP: np.ndarray, zD: np.ndarray) -> np.ndarray:
    """§6 detector: S_u = z(G) + z(p) - z(δ). (Feeds HELD ΔTPR — not run pre-ratification.)"""
    return np.asarray(zG) + np.asarray(zP) - np.asarray(zD)
