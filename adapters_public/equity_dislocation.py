

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

PRIMARY_SYMBOLS = ["SPY", "QQQ", "IWM", "VXX", "UVXY", "SVXY"]
DEFAULT_RETURN_COL = "log_return"
EPS = 1e-12


@dataclass(frozen=True)
class LoopzeroThresholds:
    eps_g: float = 0.02
    tau_delta: float = 0.0
    tau_p: float = 0.0
    delta_window: int = 30
    p_window: int = 30
    g_window: int = 30
    p_min: float = 0.0


def _validate_columns(df: pd.DataFrame, required: Iterable[str], *, name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def _safe_entropy(weights: np.ndarray) -> float:
    weights = np.asarray(weights, dtype=float)
    weights = weights[weights > 0]
    if weights.size == 0:
        return 0.0
    probs = weights / weights.sum()
    return float(-(probs * np.log(probs + EPS)).sum())


def _normalized_entropy(weights: np.ndarray) -> float:
    weights = np.asarray(weights, dtype=float)
    positive = weights[weights > 0]
    if positive.size <= 1:
        return 0.0
    ent = _safe_entropy(positive)
    return float(ent / np.log(len(positive)))


def build_market_state_panel(
    panel: pd.DataFrame,
    *,
    symbols: list[str] | None = None,
    return_col: str = DEFAULT_RETURN_COL,
) -> pd.DataFrame:
    """
    Convert the canonical long equity panel into a wide return panel indexed by ts_utc.

    Expected input columns:
      - ts_utc
      - symbol
      - close

    Returns a wide DataFrame with:
      - index: ts_utc (UTC-aware pandas timestamps)
      - columns: one return column per symbol
    """
    _validate_columns(panel, ["ts_utc", "symbol", "close"], name="panel")

    work = panel.copy()
    work["ts_utc"] = pd.to_datetime(work["ts_utc"], utc=True, errors="raise")

    chosen_symbols = symbols or PRIMARY_SYMBOLS
    work = work.loc[work["symbol"].isin(chosen_symbols)].copy()
    if work.empty:
        raise ValueError("No rows left after filtering to requested symbols")

    wide_close = (
        work.pivot_table(index="ts_utc", columns="symbol", values="close", aggfunc="last")
        .sort_index()
        .sort_index(axis=1)
    )

    log_prices = np.log(wide_close.astype(float))
    returns = log_prices.diff()
    returns.columns = [f"{col}_{return_col}" for col in returns.columns]
    returns = returns.dropna(how="all").copy()

    if returns.empty:
        raise ValueError("Wide return panel is empty after differencing")

    return returns


def compute_delta(
    market_state: pd.DataFrame,
    *,
    window: int = 30,
) -> pd.Series:
    """
    Diversity witness δ.

    For each time t, compute the correlation matrix over the trailing window,
    then convert its eigenvalue spectrum into a normalized entropy score.

    Interpretation:
      - higher δ => broader effective dimensionality / richer market state
      - lower δ => concentration / dimensional collapse
    """
    if window < 2:
        raise ValueError("window must be >= 2")
    if market_state.empty:
        raise ValueError("market_state is empty")

    values = market_state.astype(float)
    out = pd.Series(index=values.index, dtype=float, name="delta")

    for end_idx in range(window - 1, len(values)):
        block = values.iloc[end_idx - window + 1 : end_idx + 1]
        block = block.dropna(axis=1, how="all")
        if block.shape[1] <= 1:
            out.iloc[end_idx] = 0.0
            continue

        corr = block.corr().fillna(0.0).to_numpy(dtype=float)
        eigvals = np.linalg.eigvalsh(corr)
        eigvals = np.clip(eigvals, 0.0, None)
        out.iloc[end_idx] = _normalized_entropy(eigvals)

    return out.ffill().fillna(0.0)


def compute_p(
    market_state: pd.DataFrame,
    *,
    window: int = 30,
    z_threshold: float = 1.5,
) -> pd.Series:
    """
    Self-reinforcement witness p.

    We define a cross-market stress event whenever the mean absolute return across
    symbols exceeds a rolling z-threshold. Then p measures the trailing share of
    stress-event adjacency: how often a stress event follows another stress event.

    Interpretation:
      - higher p => clustered / self-reinforcing stress
      - lower p => stress dissipates instead of reappearing
    """
    if window < 2:
        raise ValueError("window must be >= 2")
    if market_state.empty:
        raise ValueError("market_state is empty")

    stress = market_state.abs().mean(axis=1)
    rolling_mean = stress.rolling(window=window, min_periods=window).mean()
    rolling_std = stress.rolling(window=window, min_periods=window).std(ddof=0)
    zscore = (stress - rolling_mean) / (rolling_std.replace(0.0, np.nan) + EPS)
    event = (zscore >= z_threshold).astype(int)
    event_lag = event.shift(1).fillna(0).astype(int)
    chained = (event & event_lag).astype(int)
    p = chained.rolling(window=window, min_periods=window).mean()
    p.name = "p"
    return p.ffill().fillna(0.0)


def compute_G(
    market_state: pd.DataFrame,
    *,
    window: int = 30,
) -> pd.Series:
    """
    Gain witness G.

    We measure local amplification as the ratio of current cross-market stress to
    the trailing mean cross-market stress over the previous window.

    Interpretation:
      - G > 1 means current stress exceeds its recent background level
      - G >= 1 + eps_g is the strict-leg witness used in the predicate
    """
    if window < 2:
        raise ValueError("window must be >= 2")
    if market_state.empty:
        raise ValueError("market_state is empty")

    stress = market_state.abs().mean(axis=1)
    baseline = stress.shift(1).rolling(window=window, min_periods=window).mean()
    gain = stress / (baseline + EPS)
    gain.name = "G"
    return gain.ffill().fillna(0.0)


def compute_loopzero_alarm(
    delta: pd.Series,
    p: pd.Series,
    G: pd.Series,
    *,
    thresholds: LoopzeroThresholds | None = None,
) -> pd.DataFrame:
    """
    Compute the Loopzero predicate fire series.

    Predicate at time t:
      - G_t >= 1 + eps_g
      - delta_t - delta_{t-delta_window} <= tau_delta
      - p_t - p_{t-p_window} >= -tau_p

    Returns a DataFrame indexed like the inputs with columns:
      - delta
      - p
      - G
      - delta_change
      - p_change
      - cond_gain
      - cond_delta
      - cond_p
      - alarm
    """
    thresholds = thresholds or LoopzeroThresholds()

    if not (delta.index.equals(p.index) and p.index.equals(G.index)):
        raise ValueError("delta, p, and G must share the same index")

    delta_change = delta - delta.shift(thresholds.delta_window)
    p_change = p - p.shift(thresholds.p_window)

    cond_gain = G >= (1.0 + thresholds.eps_g)
    cond_delta = delta_change <= thresholds.tau_delta
    cond_p = p_change >= (-thresholds.tau_p)
    alarm = cond_gain & cond_delta & cond_p

    out = pd.DataFrame(
        {
            "delta": delta,
            "p": p,
            "G": G,
            "delta_change": delta_change,
            "p_change": p_change,
            "cond_gain": cond_gain.astype(int),
            "cond_delta": cond_delta.astype(int),
            "cond_p": cond_p.astype(int),
            "alarm": alarm.astype(int),
        },
        index=delta.index,
    )
    return out


def compute_market_adapter_outputs(
    panel: pd.DataFrame,
    *,
    symbols: list[str] | None = None,
    return_col: str = DEFAULT_RETURN_COL,
    thresholds: LoopzeroThresholds | None = None,
) -> pd.DataFrame:
    """
    Convenience wrapper that runs the full adapter stack from canonical panel to alarm table.
    """
    thresholds = thresholds or LoopzeroThresholds()
    market_state = build_market_state_panel(panel, symbols=symbols, return_col=return_col)
    delta = compute_delta(market_state, window=thresholds.delta_window)
    p = compute_p(market_state, window=thresholds.p_window)
    G = compute_G(market_state, window=thresholds.g_window)
    return compute_loopzero_alarm(delta, p, G, thresholds=thresholds)