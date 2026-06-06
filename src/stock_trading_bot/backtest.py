"""Backtest a factor-rotation stock strategy over a multi-symbol price history.

The engine ranks the universe by a (possibly composite) factor score, sizes the
chosen names by the configured weighting scheme, optionally applies portfolio
volatility targeting, and rebalances on the configured schedule — tracking the
full equity curve so a rich performance report can be produced.

The original ``run_backtest`` helper is preserved for backward compatibility and
now delegates to the configurable :func:`run_strategy` engine.

Part of Stock Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from stock_trading_bot.config import (
    RebalanceSchedule,
    StrategyConfig,
    WeightingScheme,
)
from stock_trading_bot.factors import select_top_composite
from stock_trading_bot.metrics import PerformanceReport, performance_report
from stock_trading_bot.portfolio import Portfolio
from stock_trading_bot.risk import (
    equal_weight,
    inverse_vol_weight,
    scale_weights,
    volatility_target_leverage,
)
from stock_trading_bot.screener import select_top


@dataclass(slots=True)
class BacktestResult:
    """Summary of a factor-rotation backtest."""

    starting_equity: float
    final_equity: float
    equity_curve: list[float] = field(default_factory=list)
    rebalances: int = 0
    config: StrategyConfig | None = None

    @property
    def total_return_pct(self) -> float:
        if self.starting_equity == 0:
            return 0.0
        return (self.final_equity / self.starting_equity - 1.0) * 100.0

    def metrics(self, periods_per_year: int = 252) -> PerformanceReport:
        """Headline performance/risk metrics for the equity curve."""
        risk_free = self.config.risk_free if self.config else 0.0
        return performance_report(
            self.equity_curve,
            risk_free=risk_free,
            periods_per_year=periods_per_year,
        )


def _target_weights(
    targets: Sequence[str],
    window: Mapping[str, Sequence[float]],
    config: StrategyConfig,
) -> dict[str, float]:
    """Build position weights for ``targets`` per the config's risk settings."""
    if not targets:
        return {}
    if config.weighting is WeightingScheme.INVERSE_VOL:
        weights = inverse_vol_weight(targets, window, lookback=config.lookback)
    else:
        weights = equal_weight(targets)

    if config.target_vol is not None:
        leverage = volatility_target_leverage(
            weights,
            window,
            target_vol=config.target_vol,
            lookback=config.lookback,
            max_leverage=config.max_leverage,
        )
        weights = scale_weights(weights, leverage)
    return weights


def run_strategy(
    price_history: Mapping[str, Sequence[float]],
    config: StrategyConfig | None = None,
) -> BacktestResult:
    """Run a configurable factor-rotation backtest.

    Walks the aligned price series bar by bar; on each scheduled rebalance it
    ranks the universe by the composite factor score, picks the top names,
    sizes them per the weighting scheme (with optional vol targeting), and
    marks the portfolio to market on every bar.
    """
    config = config or StrategyConfig()
    symbols = list(price_history)
    length = min((len(price_history[s]) for s in symbols), default=0)
    portfolio = Portfolio(cash=config.starting_cash)
    result = BacktestResult(
        starting_equity=config.starting_cash,
        final_equity=config.starting_cash,
        config=config,
    )

    every = config.rebalance_every
    for t in range(length):
        prices = {s: price_history[s][t] for s in symbols}
        if t >= config.lookback and t % every == 0:
            window = {s: price_history[s][: t + 1] for s in symbols}
            targets = select_top_composite(
                window,
                config.factor_weights,
                top_n=config.top_n,
                lookback=config.lookback,
                min_score=config.min_score,
            )
            weights = _target_weights(targets, window, config)
            portfolio.rebalance_weighted(weights, prices)
            result.rebalances += 1
        result.equity_curve.append(portfolio.value(prices))

    result.final_equity = result.equity_curve[-1] if result.equity_curve else config.starting_cash
    return result


def run_backtest(
    price_history: Mapping[str, Sequence[float]],
    top_n: int = 3,
    lookback: int = 20,
    rebalance_every: int = 5,
    starting_cash: float = 100_000.0,
) -> BacktestResult:
    """Backward-compatible plain momentum rotation (equal weight).

    Kept for existing callers; delegates to :func:`run_strategy`. The legacy
    ``rebalance_every`` argument maps onto the closest fixed schedule and, when
    it does not match a named cadence, the engine still walks bar by bar with
    that exact cadence via a direct loop.
    """
    schedule = {
        1: RebalanceSchedule.DAILY,
        5: RebalanceSchedule.WEEKLY,
        21: RebalanceSchedule.MONTHLY,
    }
    if rebalance_every in schedule:
        config = StrategyConfig(
            top_n=top_n,
            lookback=lookback,
            starting_cash=starting_cash,
            factor_weights={"momentum": 1.0},
            schedule=schedule[rebalance_every],
        )
        return run_strategy(price_history, config)

    # Custom cadence not covered by a named schedule: run the simple loop.
    symbols = list(price_history)
    length = min((len(price_history[s]) for s in symbols), default=0)
    portfolio = Portfolio(cash=starting_cash)
    result = BacktestResult(starting_equity=starting_cash, final_equity=starting_cash)
    for t in range(length):
        prices = {s: price_history[s][t] for s in symbols}
        if t >= lookback and t % rebalance_every == 0:
            window = {s: price_history[s][: t + 1] for s in symbols}
            targets = select_top(window, top_n=top_n, lookback=lookback)
            portfolio.rebalance(targets, prices)
            result.rebalances += 1
        result.equity_curve.append(portfolio.value(prices))
    result.final_equity = result.equity_curve[-1] if result.equity_curve else starting_cash
    return result
