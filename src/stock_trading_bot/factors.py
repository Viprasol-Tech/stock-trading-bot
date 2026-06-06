"""Equity factor library and composite cross-sectional scoring.

Beyond plain momentum, this module ships three well-studied equity factors and a
composite scorer that blends them with configurable weights:

* **Momentum** — trailing return; "buy the winners".
* **Low volatility** — the low-volatility anomaly; calmer stocks have
  historically delivered strong risk-adjusted returns. Scored as *negative*
  realized volatility so that lower vol ranks higher.
* **Value (mean-reversion proxy)** — distance of the latest price below its own
  moving average. Without fundamentals we proxy "cheapness" by how far a name
  has pulled back from its trend, a classic short-horizon value/reversal signal.

Each factor returns a raw score per symbol; the composite cross-sectionally
z-scores every factor (so they share a common scale) and combines them.

Part of Stock Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Mapping, Sequence

PriceSeries = Sequence[float]
Universe = Mapping[str, PriceSeries]


def momentum(prices: PriceSeries, lookback: int = 20) -> float:
    """Trailing return over ``lookback`` bars (0.0 if not enough history)."""
    if len(prices) <= lookback or prices[-lookback - 1] == 0:
        return 0.0
    return prices[-1] / prices[-lookback - 1] - 1.0


def _returns(prices: PriceSeries, lookback: int) -> list[float]:
    window = list(prices[-(lookback + 1) :])
    out: list[float] = []
    for prev, cur in itertools.pairwise(window):
        if prev != 0:
            out.append(cur / prev - 1.0)
    return out


def volatility(prices: PriceSeries, lookback: int = 20) -> float:
    """Sample standard deviation of simple returns over ``lookback`` bars."""
    rets = _returns(prices, lookback)
    if len(rets) < 2:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var)


def low_volatility(prices: PriceSeries, lookback: int = 20) -> float:
    """Low-volatility factor: ``-volatility`` so calmer stocks score higher."""
    return -volatility(prices, lookback)


def value(prices: PriceSeries, lookback: int = 20) -> float:
    """Mean-reversion value proxy: how far price sits below its own SMA.

    Positive when the latest price is *below* its moving average (cheap /
    pulled back), negative when it is stretched above. Expressed as a fraction
    of the moving average so it is comparable across price levels.
    """
    if len(prices) < lookback or lookback <= 0:
        return 0.0
    window = list(prices[-lookback:])
    sma = sum(window) / len(window)
    if sma == 0:
        return 0.0
    return (sma - prices[-1]) / sma


#: Registry of available single-name factor functions, keyed by name.
FACTOR_FUNCS: dict[str, Callable[[PriceSeries, int], float]] = {
    "momentum": momentum,
    "low_vol": low_volatility,
    "value": value,
}


def factor_scores(
    universe: Universe,
    factor: str,
    lookback: int = 20,
) -> dict[str, float]:
    """Raw scores for one named factor across the universe."""
    try:
        func = FACTOR_FUNCS[factor]
    except KeyError as exc:  # pragma: no cover - defensive
        raise ValueError(f"unknown factor {factor!r}; choose from {sorted(FACTOR_FUNCS)}") from exc
    return {sym: func(prices, lookback) for sym, prices in universe.items()}


def zscore(scores: Mapping[str, float]) -> dict[str, float]:
    """Cross-sectional z-score of a mapping of raw scores.

    Returns all-zero scores when there is no dispersion (degenerate input),
    which keeps the composite well-defined for flat factors.
    """
    values = list(scores.values())
    n = len(values)
    if n == 0:
        return {}
    mean = sum(values) / n
    if n == 1:
        return dict.fromkeys(scores, 0.0)
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    std = math.sqrt(var)
    if std == 0:
        return dict.fromkeys(scores, 0.0)
    return {sym: (v - mean) / std for sym, v in scores.items()}


def composite_scores(
    universe: Universe,
    weights: Mapping[str, float],
    lookback: int = 20,
) -> dict[str, float]:
    """Blend several factors into a single cross-sectional score per symbol.

    ``weights`` maps factor names (see :data:`FACTOR_FUNCS`) to blend weights.
    Each factor is z-scored before weighting so no single factor dominates by
    virtue of its raw scale.
    """
    if not weights:
        raise ValueError("composite_scores requires at least one weighted factor")
    total = dict.fromkeys(universe, 0.0)
    for factor, weight in weights.items():
        if weight == 0:
            continue
        z = zscore(factor_scores(universe, factor, lookback))
        for sym, score in z.items():
            total[sym] += weight * score
    return total


def rank_by_composite(
    universe: Universe,
    weights: Mapping[str, float],
    lookback: int = 20,
) -> list[tuple[str, float]]:
    """``(symbol, composite_score)`` pairs sorted strongest-first."""
    scored = composite_scores(universe, weights, lookback)
    return sorted(scored.items(), key=lambda item: item[1], reverse=True)


def select_top_composite(
    universe: Universe,
    weights: Mapping[str, float],
    top_n: int,
    lookback: int = 20,
    min_score: float = 0.0,
) -> list[str]:
    """Top ``top_n`` symbols by composite score above ``min_score``."""
    ranked = rank_by_composite(universe, weights, lookback)
    return [sym for sym, score in ranked if score > min_score][:top_n]
