"""Tests for position sizing and volatility targeting."""

from __future__ import annotations

import math

from stock_trading_bot.risk import (
    annualized_volatility,
    equal_weight,
    inverse_vol_weight,
    portfolio_volatility,
    scale_weights,
    volatility_target_leverage,
)


def _series(noise: float, n: int = 60) -> list[float]:
    return [100 + 0.1 * i + noise * math.sin(i) for i in range(n)]


def test_equal_weight_sums_to_one() -> None:
    w = equal_weight(["A", "B", "C", "D"])
    assert math.isclose(sum(w.values()), 1.0)
    assert all(math.isclose(v, 0.25) for v in w.values())


def test_equal_weight_empty() -> None:
    assert equal_weight([]) == {}


def test_inverse_vol_weight_favors_calmer_name() -> None:
    history = {"CALM": _series(1.0), "WILD": _series(10.0)}
    w = inverse_vol_weight(["CALM", "WILD"], history, lookback=20)
    assert math.isclose(sum(w.values()), 1.0, rel_tol=1e-9)
    assert w["CALM"] > w["WILD"]


def test_inverse_vol_weight_empty() -> None:
    assert inverse_vol_weight([], {}, lookback=20) == {}


def test_inverse_vol_floor_on_flat_series() -> None:
    history = {"FLAT": [100.0] * 60}
    w = inverse_vol_weight(["FLAT"], history, lookback=20)
    assert math.isclose(w["FLAT"], 1.0)


def test_annualized_volatility_scales_up() -> None:
    prices = _series(5.0)
    assert annualized_volatility(prices, 20) > 0


def test_portfolio_volatility_combines_positions() -> None:
    history = {"A": _series(5.0), "B": _series(5.0)}
    weights = {"A": 0.5, "B": 0.5}
    pv = portfolio_volatility(weights, history, lookback=20)
    assert pv > 0


def test_vol_target_leverage_clamped_to_max() -> None:
    # Very low (but non-zero) vol -> wants huge leverage -> clamped to max.
    history = {"CALM": _series(0.05)}
    lev = volatility_target_leverage(
        {"CALM": 1.0}, history, target_vol=0.50, lookback=20, max_leverage=2.0
    )
    assert lev == 2.0


def test_vol_target_leverage_zero_when_no_risk() -> None:
    history = {"FLAT": [100.0] * 60}  # zero vol -> leverage undefined -> 0.0
    lev = volatility_target_leverage(
        {"FLAT": 1.0}, history, target_vol=0.15, lookback=20, max_leverage=2.0
    )
    assert lev == 0.0


def test_vol_target_leverage_derisks_high_vol() -> None:
    history = {"WILD": _series(20.0)}
    lev = volatility_target_leverage(
        {"WILD": 1.0}, history, target_vol=0.10, lookback=20, max_leverage=3.0
    )
    assert 0.0 < lev < 1.0


def test_scale_weights_multiplies() -> None:
    scaled = scale_weights({"A": 0.5, "B": 0.5}, 1.5)
    assert math.isclose(scaled["A"], 0.75)
    assert math.isclose(scaled["B"], 0.75)
