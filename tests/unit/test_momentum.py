"""Tests for the screener, portfolio, and momentum-rotation backtest."""

from __future__ import annotations

import math

from stock_trading_bot.backtest import run_backtest
from stock_trading_bot.portfolio import Portfolio
from stock_trading_bot.screener import momentum, rank_by_momentum, select_top


def test_momentum_positive_on_uptrend() -> None:
    assert momentum([100, 105, 110, 120], lookback=3) > 0


def test_momentum_zero_without_history() -> None:
    assert momentum([100, 101], lookback=5) == 0.0


def test_rank_orders_strongest_first() -> None:
    universe = {"UP": [100, 110, 130], "FLAT": [100, 100, 100], "DOWN": [100, 95, 80]}
    ranked = rank_by_momentum(universe, lookback=2)
    assert ranked[0][0] == "UP"
    assert ranked[-1][0] == "DOWN"


def test_select_top_filters_and_limits() -> None:
    universe = {"UP": [100, 110, 130], "FLAT": [100, 100, 100], "DOWN": [100, 95, 80]}
    picked = select_top(universe, top_n=2, lookback=2)
    assert picked == ["UP"]  # only UP has positive momentum


def test_portfolio_rebalance_equal_weight() -> None:
    p = Portfolio(cash=10_000.0)
    p.rebalance(["A", "B"], {"A": 100.0, "B": 50.0})
    # Equal weight: ~5,000 each -> 50 shares A, 100 shares B; cash ~0.
    assert math.isclose(p.shares["A"] * 100, 5_000.0, rel_tol=1e-6)
    assert math.isclose(p.shares["B"] * 50, 5_000.0, rel_tol=1e-6)
    assert math.isclose(p.value({"A": 100.0, "B": 50.0}), 10_000.0, rel_tol=1e-6)


def test_backtest_runs_and_tracks_equity() -> None:
    universe = {
        "AAA": [100 + i for i in range(60)],
        "BBB": [100 + 0.1 * i for i in range(60)],
        "CCC": [100 - 0.2 * i for i in range(60)],
    }
    result = run_backtest(universe, top_n=1, lookback=10, rebalance_every=5)
    assert len(result.equity_curve) == 60
    assert isinstance(result.total_return_pct, float)
