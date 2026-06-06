"""Performance and risk metrics computed from an equity curve.

Pure-Python (no numpy required) implementations of the metrics every quant
report needs: CAGR, annualized volatility, Sharpe, Sortino, max drawdown, Calmar
and win rate. All take an equity curve (a list of portfolio values over time).

Part of Stock Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass

TRADING_DAYS = 252


def returns_from_equity(equity: Sequence[float]) -> list[float]:
    """Per-bar simple returns from an equity curve."""
    out: list[float] = []
    for prev, cur in itertools.pairwise(equity):
        if prev != 0:
            out.append(cur / prev - 1.0)
    return out


def total_return(equity: Sequence[float]) -> float:
    """Cumulative return over the whole curve (fraction, e.g. 0.25 = +25%)."""
    if len(equity) < 2 or equity[0] == 0:
        return 0.0
    return equity[-1] / equity[0] - 1.0


def cagr(equity: Sequence[float], periods_per_year: int = TRADING_DAYS) -> float:
    """Compound annual growth rate implied by the curve length."""
    if len(equity) < 2 or equity[0] <= 0 or equity[-1] <= 0:
        return 0.0
    years = (len(equity) - 1) / periods_per_year
    if years <= 0:
        return 0.0
    growth = equity[-1] / equity[0]
    return float(math.pow(growth, 1.0 / years)) - 1.0


def volatility(equity: Sequence[float], periods_per_year: int = TRADING_DAYS) -> float:
    """Annualized standard deviation of per-bar returns."""
    rets = returns_from_equity(equity)
    if len(rets) < 2:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(periods_per_year)


def sharpe_ratio(
    equity: Sequence[float],
    risk_free: float = 0.0,
    periods_per_year: int = TRADING_DAYS,
) -> float:
    """Annualized Sharpe ratio (excess return per unit of total volatility)."""
    rets = returns_from_equity(equity)
    if len(rets) < 2:
        return 0.0
    rf_per_bar = risk_free / periods_per_year
    excess = [r - rf_per_bar for r in rets]
    mean = sum(excess) / len(excess)
    var = sum((r - mean) ** 2 for r in excess) / (len(excess) - 1)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    return (mean / std) * math.sqrt(periods_per_year)


def sortino_ratio(
    equity: Sequence[float],
    risk_free: float = 0.0,
    periods_per_year: int = TRADING_DAYS,
) -> float:
    """Annualized Sortino ratio (excess return per unit of downside deviation)."""
    rets = returns_from_equity(equity)
    if len(rets) < 2:
        return 0.0
    rf_per_bar = risk_free / periods_per_year
    excess = [r - rf_per_bar for r in rets]
    mean = sum(excess) / len(excess)
    downside = [min(r, 0.0) ** 2 for r in excess]
    dd = math.sqrt(sum(downside) / len(downside))
    if dd == 0:
        return 0.0
    return (mean / dd) * math.sqrt(periods_per_year)


def max_drawdown(equity: Sequence[float]) -> float:
    """Largest peak-to-trough decline as a negative fraction (e.g. -0.20)."""
    peak = -math.inf
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            dd = value / peak - 1.0
            worst = min(worst, dd)
    return worst


def calmar_ratio(equity: Sequence[float], periods_per_year: int = TRADING_DAYS) -> float:
    """CAGR divided by the magnitude of max drawdown."""
    mdd = abs(max_drawdown(equity))
    if mdd == 0:
        return 0.0
    return cagr(equity, periods_per_year) / mdd


def win_rate(equity: Sequence[float]) -> float:
    """Fraction of bars with a positive return (0.0..1.0)."""
    rets = returns_from_equity(equity)
    if not rets:
        return 0.0
    wins = sum(1 for r in rets if r > 0)
    return wins / len(rets)


@dataclass(slots=True)
class PerformanceReport:
    """Bundle of headline metrics for an equity curve."""

    total_return: float
    cagr: float
    volatility: float
    sharpe: float
    sortino: float
    max_drawdown: float
    calmar: float
    win_rate: float

    def as_dict(self) -> dict[str, float]:
        return {
            "total_return": self.total_return,
            "cagr": self.cagr,
            "volatility": self.volatility,
            "sharpe": self.sharpe,
            "sortino": self.sortino,
            "max_drawdown": self.max_drawdown,
            "calmar": self.calmar,
            "win_rate": self.win_rate,
        }


def performance_report(
    equity: Sequence[float],
    risk_free: float = 0.0,
    periods_per_year: int = TRADING_DAYS,
) -> PerformanceReport:
    """Compute all headline metrics from an equity curve in one call."""
    return PerformanceReport(
        total_return=total_return(equity),
        cagr=cagr(equity, periods_per_year),
        volatility=volatility(equity, periods_per_year),
        sharpe=sharpe_ratio(equity, risk_free, periods_per_year),
        sortino=sortino_ratio(equity, risk_free, periods_per_year),
        max_drawdown=max_drawdown(equity),
        calmar=calmar_ratio(equity, periods_per_year),
        win_rate=win_rate(equity),
    )
