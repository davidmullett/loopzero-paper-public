"""§8 cluster-aware BCa bootstrap at USER grain (each unit = one user = one cluster).

Index-based & vectorized: the statistic receives an array of unit indices (with
replacement for bootstrap; leave-one-out for jackknife acceleration), so callers
can compute it on numpy arrays without rebuilding object lists. BCa 95% CI,
10,000 iters, seed 201 (§8/§13). Determinism: numpy Generator(PCG64) seeded.
"""
from __future__ import annotations
from typing import Callable, Tuple
import numpy as np
from scipy.stats import norm


def bca_ci(
    n: int,
    statistic: Callable[[np.ndarray], float],
    *,
    n_boot: int = 10_000,
    seed: int = 201,
    alpha: float = 0.05,
) -> Tuple[float, float, float]:
    """statistic(idx_array) -> float. Returns (theta_hat, lo, hi) BCa CI over n units."""
    all_idx = np.arange(n)
    theta_hat = float(statistic(all_idx))
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot, float)
    for b in range(n_boot):
        boots[b] = statistic(rng.integers(0, n, size=n))
    boots.sort()

    prop = float(np.mean(boots < theta_hat))
    prop = min(max(prop, 1.0 / (n_boot + 1)), 1.0 - 1.0 / (n_boot + 1))
    z0 = norm.ppf(prop)

    jack = np.empty(n, float)
    for i in range(n):
        jack[i] = statistic(np.delete(all_idx, i))
    jbar = jack.mean()
    num = np.sum((jbar - jack) ** 3)
    den = 6.0 * (np.sum((jbar - jack) ** 2) ** 1.5)
    a = num / den if den != 0 else 0.0

    zl, zu = norm.ppf(alpha / 2), norm.ppf(1 - alpha / 2)
    adj = lambda z: norm.cdf(z0 + (z0 + z) / (1 - a * (z0 + z)))
    lo = float(np.quantile(boots, adj(zl)))
    hi = float(np.quantile(boots, adj(zu)))
    return theta_hat, lo, hi
