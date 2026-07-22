"""§9 covariate-adjustment machinery — logistic regression (IRLS) + rank AUC +
incremental AUC. Pure numpy/scipy (sklearn/statsmodels unavailable). Debugged on
label-permuted synthetic populations (chance by construction); computes no
real-engine quantity by itself.
"""
from __future__ import annotations
from typing import Tuple
import numpy as np
from scipy.stats import rankdata


def logistic_fit(X: np.ndarray, y: np.ndarray, *, l2: float = 1.0, iters: int = 200) -> np.ndarray:
    """Ridge-regularised logistic regression via IRLS/Newton. X includes an intercept
    column (column 0). Non-intercept columns are standardised internally so the ridge
    penalty is scale-consistent and separable resamples cannot blow the coefficients
    up (sign of each coefficient and the induced AUC are invariant to this scaling).
    Coefficients are returned on the STANDARDISED scale (sufficient for §9 sign tests
    and AUC). Deterministic."""
    X = np.asarray(X, float); y = np.asarray(y, float)
    n, d = X.shape
    mu = np.zeros(d); sd = np.ones(d)
    if d > 1:
        mu[1:] = X[:, 1:].mean(axis=0)
        sd[1:] = np.where(X[:, 1:].std(axis=0) > 1e-12, X[:, 1:].std(axis=0), 1.0)
    Xs = (X - mu) / sd
    pen = np.ones(d); pen[0] = 0.0  # do not penalise the intercept
    beta = np.zeros(d)
    # np.errstate silences spurious fp-flag warnings numpy 2.x raises from the matmul
    # SIMD loop on some layouts; the finiteness assert below catches any REAL divergence.
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        for _ in range(iters):
            eta = np.clip(Xs @ beta, -30.0, 30.0)
            p = 1.0 / (1.0 + np.exp(-eta))
            w = np.clip(p * (1.0 - p), 1e-9, None)
            H = (Xs.T * w) @ Xs + l2 * np.diag(pen)
            g = Xs.T @ (y - p) - l2 * pen * beta
            step = np.linalg.solve(H, g)
            beta = beta + step
            if np.max(np.abs(step)) < 1e-9:
                break
    assert np.all(np.isfinite(beta)), "logistic IRLS diverged (non-finite coefficients)"
    return beta


def linear_predictor(X: np.ndarray, beta: np.ndarray) -> np.ndarray:
    """Standardised linear predictor consistent with logistic_fit's internal scaling."""
    X = np.asarray(X, float); d = X.shape[1]
    mu = np.zeros(d); sd = np.ones(d)
    if d > 1:
        mu[1:] = X[:, 1:].mean(axis=0)
        sd[1:] = np.where(X[:, 1:].std(axis=0) > 1e-12, X[:, 1:].std(axis=0), 1.0)
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        return ((X - mu) / sd) @ beta


def auc(scores: np.ndarray, y: np.ndarray) -> float:
    """Rank-based AUC (Mann–Whitney), tie-corrected. AUC is invariant to any monotone
    transform of `scores`, so the logistic linear predictor may be passed directly."""
    scores = np.asarray(scores, float); y = np.asarray(y, int)
    n_pos = int((y == 1).sum()); n_neg = int((y == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    r = rankdata(scores)
    return float((r[y == 1].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def _design(cov: np.ndarray, ind: np.ndarray | None) -> np.ndarray:
    n = cov.shape[0]
    cols = [np.ones((n, 1)), cov]
    if ind is not None:
        cols.append(ind)
    return np.hstack(cols)


def incremental_auc(cov: np.ndarray, ind: np.ndarray, y: np.ndarray) -> float:
    """AUC(full = covariates + indicators z(G),z(p),z(δ)) − AUC(covariates-only).
    Both models fit on the SAME rows; AUC evaluated in-sample (§9 is on the eval fold)."""
    Xf = _design(cov, ind)
    Xc = _design(cov, None)
    bf = logistic_fit(Xf, y)
    bc = logistic_fit(Xc, y)
    return auc(linear_predictor(Xf, bf), y) - auc(linear_predictor(Xc, bc), y)


def zscore(x: np.ndarray, ref_mean: float, ref_sd: float) -> np.ndarray:
    x = np.asarray(x, float)
    return (x - ref_mean) / ref_sd if ref_sd > 0 else np.zeros_like(x)
