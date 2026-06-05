"""Backtest a momentum-rotation stock strategy over a multi-symbol price history.

Every ``rebalance_every`` bars, rank the universe by momentum, hold the top-N
equal-weighted, and track the portfolio value.

Part of Stock Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from stock_trading_bot.portfolio import Portfolio
from stock_trading_bot.screener import select_top


@dataclass(slots=True)
class BacktestResult:
    """Summary of a momentum-rotation backtest."""

    starting_equity: float
    final_equity: float
    equity_curve: list[float] = field(default_factory=list)

    @property
    def total_return_pct(self) -> float:
        if self.starting_equity == 0:
            return 0.0
        return (self.final_equity / self.starting_equity - 1.0) * 100.0


def run_backtest(
    price_history: Mapping[str, Sequence[float]],
    top_n: int = 3,
    lookback: int = 20,
    rebalance_every: int = 5,
    starting_cash: float = 100_000.0,
) -> BacktestResult:
    """Run a top-N momentum rotation over aligned per-symbol price series."""
    symbols = list(price_history)
    length = min(len(price_history[s]) for s in symbols) if symbols else 0
    portfolio = Portfolio(cash=starting_cash)
    result = BacktestResult(starting_equity=starting_cash, final_equity=starting_cash)

    for t in range(length):
        prices = {s: price_history[s][t] for s in symbols}
        if t >= lookback and t % rebalance_every == 0:
            window = {s: price_history[s][: t + 1] for s in symbols}
            targets = select_top(window, top_n=top_n, lookback=lookback)
            portfolio.rebalance(targets, prices)
        result.equity_curve.append(portfolio.value(prices))

    result.final_equity = result.equity_curve[-1] if result.equity_curve else starting_cash
    return result
