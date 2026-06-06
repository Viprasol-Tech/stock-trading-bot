"""Tests for the paper portfolio (equal-weight and weighted rebalancing)."""

from __future__ import annotations

import math

from stock_trading_bot.portfolio import Portfolio


def test_initial_value_is_cash() -> None:
    p = Portfolio(cash=50_000.0)
    assert p.value({"A": 100.0}) == 50_000.0


def test_rebalance_equal_weight() -> None:
    p = Portfolio(cash=10_000.0)
    p.rebalance(["A", "B"], {"A": 100.0, "B": 50.0})
    assert math.isclose(p.shares["A"] * 100, 5_000.0, rel_tol=1e-6)
    assert math.isclose(p.shares["B"] * 50, 5_000.0, rel_tol=1e-6)
    assert math.isclose(p.value({"A": 100.0, "B": 50.0}), 10_000.0, rel_tol=1e-6)


def test_rebalance_empty_goes_to_cash() -> None:
    p = Portfolio(cash=10_000.0)
    p.rebalance(["A"], {"A": 100.0})
    p.rebalance([], {"A": 110.0})
    assert p.shares["A"] == 0.0
    assert math.isclose(p.value({"A": 110.0}), p.cash, rel_tol=1e-9)


def test_rebalance_liquidates_dropped_symbol() -> None:
    p = Portfolio(cash=10_000.0)
    p.rebalance(["A", "B"], {"A": 100.0, "B": 100.0})
    p.rebalance(["A"], {"A": 100.0, "B": 100.0})
    assert p.shares["B"] == 0.0
    assert math.isclose(p.shares["A"] * 100, p.value({"A": 100.0, "B": 100.0}), rel_tol=1e-6)


def test_rebalance_weighted_respects_weights() -> None:
    p = Portfolio(cash=10_000.0)
    p.rebalance_weighted({"A": 0.7, "B": 0.3}, {"A": 100.0, "B": 100.0})
    assert math.isclose(p.shares["A"] * 100, 7_000.0, rel_tol=1e-6)
    assert math.isclose(p.shares["B"] * 100, 3_000.0, rel_tol=1e-6)


def test_rebalance_weighted_partial_leaves_cash() -> None:
    p = Portfolio(cash=10_000.0)
    # Weights sum to 0.5 -> half invested, half cash (vol-target de-risk).
    p.rebalance_weighted({"A": 0.5}, {"A": 100.0})
    assert math.isclose(p.shares["A"] * 100, 5_000.0, rel_tol=1e-6)
    assert math.isclose(p.cash, 5_000.0, rel_tol=1e-6)


def test_rebalance_skips_zero_price() -> None:
    p = Portfolio(cash=10_000.0)
    p.rebalance_weighted({"A": 1.0}, {"A": 0.0})
    assert p.shares.get("A", 0.0) == 0.0
    assert math.isclose(p.cash, 10_000.0)
