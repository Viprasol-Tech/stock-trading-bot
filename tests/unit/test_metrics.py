"""Tests for performance and risk metrics."""

from __future__ import annotations

import math

from stock_trading_bot.metrics import (
    cagr,
    calmar_ratio,
    max_drawdown,
    performance_report,
    returns_from_equity,
    sharpe_ratio,
    sortino_ratio,
    total_return,
    volatility,
    win_rate,
)


def test_returns_from_equity() -> None:
    rets = returns_from_equity([100, 110, 99])
    assert math.isclose(rets[0], 0.1, rel_tol=1e-9)
    assert math.isclose(rets[1], -0.1, rel_tol=1e-9)


def test_total_return() -> None:
    assert math.isclose(total_return([100, 120]), 0.2, rel_tol=1e-9)


def test_total_return_short_curve() -> None:
    assert total_return([100]) == 0.0


def test_cagr_positive_on_growth() -> None:
    curve = [100.0 * (1.001**i) for i in range(252)]
    assert cagr(curve) > 0


def test_cagr_zero_on_short() -> None:
    assert cagr([100]) == 0.0


def test_volatility_nonnegative() -> None:
    curve = [100 + (1 if i % 2 else -1) for i in range(50)]
    assert volatility(curve) > 0


def test_sharpe_zero_on_flat() -> None:
    assert sharpe_ratio([100.0] * 30) == 0.0


def test_sharpe_positive_on_steady_growth() -> None:
    curve = [100.0 * (1.001**i) for i in range(100)]
    assert sharpe_ratio(curve) > 0


def test_sortino_ignores_upside_vol() -> None:
    # All-positive returns -> no downside deviation -> 0.0 by convention.
    curve = [100.0 * (1.01**i) for i in range(30)]
    assert sortino_ratio(curve) == 0.0


def test_max_drawdown_negative() -> None:
    curve = [100, 120, 90, 130]
    dd = max_drawdown(curve)
    assert math.isclose(dd, 90 / 120 - 1.0, rel_tol=1e-9)
    assert dd < 0


def test_max_drawdown_zero_on_monotonic() -> None:
    assert max_drawdown([100, 110, 120]) == 0.0


def test_calmar_zero_without_drawdown() -> None:
    assert calmar_ratio([100, 110, 120]) == 0.0


def test_win_rate_counts_up_bars() -> None:
    assert math.isclose(win_rate([100, 110, 105, 115]), 2 / 3, rel_tol=1e-9)


def test_win_rate_empty() -> None:
    assert win_rate([100]) == 0.0


def test_performance_report_bundles_all() -> None:
    curve = [100.0 * (1.0005**i) for i in range(252)]
    report = performance_report(curve)
    d = report.as_dict()
    assert set(d) == {
        "total_return",
        "cagr",
        "volatility",
        "sharpe",
        "sortino",
        "max_drawdown",
        "calmar",
        "win_rate",
    }
    assert report.total_return > 0
