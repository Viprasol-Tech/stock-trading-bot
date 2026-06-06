"""Position-sizing schemes: equal weight, inverse-volatility (risk parity),
and portfolio-level volatility targeting.

These turn a *selection* of symbols into a *weight* per symbol:

* **equal_weight** — 1/N across the basket.
* **inverse_vol_weight** — risk-parity style: weight inversely proportional to
  each name's realized volatility so calmer names get a larger share and every
  position contributes a similar amount of risk.
* **volatility_target_leverage** — scales gross exposure up or down so the
  blended portfolio volatility matches an annualized target.

Part of Stock Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from stock_trading_bot.factors import volatility

PriceSeries = Sequence[float]
Universe = Mapping[str, PriceSeries]

#: Trading days per year, used to annualize per-bar volatility.
TRADING_DAYS = 252


def equal_weight(symbols: Sequence[str]) -> dict[str, float]:
    """Equal weights summing to 1.0 (empty basket -> empty mapping)."""
    if not symbols:
        return {}
    w = 1.0 / len(symbols)
    return dict.fromkeys(symbols, w)


def inverse_vol_weight(
    symbols: Sequence[str],
    history: Universe,
    lookback: int = 20,
    floor_vol: float = 1e-4,
) -> dict[str, float]:
    """Risk-parity weights inversely proportional to each name's volatility.

    Volatility is floored at ``floor_vol`` to avoid divide-by-zero for flat
    series. Weights are normalized to sum to 1.0. Falls back to equal weight
    when no usable volatility is available.
    """
    if not symbols:
        return {}
    inv: dict[str, float] = {}
    for sym in symbols:
        vol = max(volatility(history.get(sym, ()), lookback), floor_vol)
        inv[sym] = 1.0 / vol
    total = sum(inv.values())
    if total <= 0:  # pragma: no cover - defensive
        return equal_weight(symbols)
    return {sym: w / total for sym, w in inv.items()}


def annualized_volatility(prices: PriceSeries, lookback: int = 20) -> float:
    """Per-bar volatility scaled to an annual figure (sqrt-time rule)."""
    return volatility(prices, lookback) * math.sqrt(TRADING_DAYS)


def portfolio_volatility(
    weights: Mapping[str, float],
    history: Universe,
    lookback: int = 20,
) -> float:
    """Annualized volatility of a weighted basket, ignoring cross-correlations.

    Uses the conservative no-correlation approximation
    ``sqrt(sum (w_i * sigma_i)^2)`` which needs only per-asset vols and is a
    sensible default when a full covariance matrix is unavailable.
    """
    acc = 0.0
    for sym, w in weights.items():
        sigma = annualized_volatility(history.get(sym, ()), lookback)
        acc += (w * sigma) ** 2
    return math.sqrt(acc)


def volatility_target_leverage(
    weights: Mapping[str, float],
    history: Universe,
    target_vol: float = 0.15,
    lookback: int = 20,
    max_leverage: float = 2.0,
) -> float:
    """Leverage multiplier that scales a basket toward ``target_vol``.

    Returns ``target_vol / portfolio_vol`` clamped to ``[0, max_leverage]``.
    A value below 1 de-risks (holds cash); above 1 gears up to the cap.
    """
    pv = portfolio_volatility(weights, history, lookback)
    if pv <= 0:
        return 0.0
    return min(target_vol / pv, max_leverage)


def scale_weights(weights: Mapping[str, float], leverage: float) -> dict[str, float]:
    """Apply a leverage multiplier to every weight."""
    return {sym: w * leverage for sym, w in weights.items()}
