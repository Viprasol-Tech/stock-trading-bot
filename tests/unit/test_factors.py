"""Tests for the equity factor library and composite scoring."""

from __future__ import annotations

import math

from stock_trading_bot.factors import (
    composite_scores,
    factor_scores,
    low_volatility,
    momentum,
    rank_by_composite,
    select_top_composite,
    value,
    volatility,
    zscore,
)


def test_momentum_positive_on_uptrend() -> None:
    assert momentum([100, 105, 110, 120], lookback=3) > 0


def test_momentum_zero_without_history() -> None:
    assert momentum([100, 101], lookback=5) == 0.0


def test_volatility_zero_on_flat_series() -> None:
    assert volatility([100.0] * 30, lookback=20) == 0.0


def test_volatility_positive_on_noisy_series() -> None:
    prices = [100 + (5 if i % 2 else -5) for i in range(30)]
    assert volatility(prices, lookback=20) > 0


def test_low_vol_prefers_calmer_stock() -> None:
    calm = [100 + 0.1 * i for i in range(40)]
    wild = [100 + 0.1 * i + 10 * math.sin(i) for i in range(40)]
    assert low_volatility(calm, 20) > low_volatility(wild, 20)


def test_value_positive_when_below_sma() -> None:
    # Sharp drop on the last bar -> price below its moving average -> "cheap".
    prices = [100.0] * 19 + [80.0]
    assert value(prices, lookback=20) > 0


def test_value_negative_when_stretched_above_sma() -> None:
    prices = [100.0] * 19 + [130.0]
    assert value(prices, lookback=20) < 0


def test_value_handles_short_series() -> None:
    assert value([100.0, 101.0], lookback=20) == 0.0


def test_zscore_centers_and_scales() -> None:
    z = zscore({"a": 1.0, "b": 2.0, "c": 3.0})
    assert math.isclose(sum(z.values()), 0.0, abs_tol=1e-9)
    assert z["c"] > z["a"]


def test_zscore_flat_returns_zeros() -> None:
    z = zscore({"a": 5.0, "b": 5.0})
    assert z == {"a": 0.0, "b": 0.0}


def test_zscore_single_element() -> None:
    assert zscore({"a": 7.0}) == {"a": 0.0}


def test_factor_scores_uses_registry() -> None:
    universe = {"UP": [100, 110, 130], "DOWN": [100, 95, 80]}
    scores = factor_scores(universe, "momentum", lookback=2)
    assert scores["UP"] > scores["DOWN"]


def test_composite_blends_factors() -> None:
    universe = {
        "UP": [100 + i for i in range(40)],
        "DOWN": [100 - 0.5 * i for i in range(40)],
        "FLAT": [100.0] * 40,
    }
    scores = composite_scores(universe, {"momentum": 1.0}, lookback=20)
    assert scores["UP"] > scores["FLAT"] > scores["DOWN"]


def test_composite_zero_weight_factor_ignored() -> None:
    universe = {"A": [100 + i for i in range(40)], "B": [100 - i for i in range(40)]}
    only_mom = composite_scores(universe, {"momentum": 1.0}, lookback=20)
    with_zero = composite_scores(universe, {"momentum": 1.0, "low_vol": 0.0}, lookback=20)
    assert only_mom == with_zero


def test_rank_by_composite_orders_strongest_first() -> None:
    universe = {"UP": [100, 110, 130], "FLAT": [100, 100, 100], "DOWN": [100, 95, 80]}
    ranked = rank_by_composite(universe, {"momentum": 1.0}, lookback=2)
    assert ranked[0][0] == "UP"
    assert ranked[-1][0] == "DOWN"


def test_select_top_composite_limits_and_floors() -> None:
    universe = {
        "UP": [100 + i for i in range(40)],
        "MID": [100 + 0.05 * i for i in range(40)],
        "DOWN": [100 - i for i in range(40)],
    }
    picked = select_top_composite(universe, {"momentum": 1.0}, top_n=2, lookback=20)
    assert picked[0] == "UP"
    assert "DOWN" not in picked
