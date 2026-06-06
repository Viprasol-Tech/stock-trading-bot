"""Tests for the configurable backtest engine and legacy helper."""

from __future__ import annotations

import math

from stock_trading_bot.backtest import run_backtest, run_strategy
from stock_trading_bot.config import (
    RebalanceSchedule,
    StrategyConfig,
    WeightingScheme,
)


def _universe(n: int = 80) -> dict[str, list[float]]:
    return {
        "AAA": [100 + i for i in range(n)],
        "BBB": [100 + 0.1 * i + 3 * math.sin(i) for i in range(n)],
        "CCC": [100 - 0.2 * i for i in range(n)],
        "DDD": [100 + 0.5 * i + 6 * math.sin(i / 2) for i in range(n)],
    }


def test_legacy_run_backtest_tracks_equity() -> None:
    result = run_backtest(_universe(), top_n=1, lookback=10, rebalance_every=5)
    assert len(result.equity_curve) == 80
    assert isinstance(result.total_return_pct, float)
    assert result.rebalances > 0


def test_legacy_custom_cadence_path() -> None:
    # rebalance_every=7 is not a named schedule -> exercises the fallback loop.
    result = run_backtest(_universe(), top_n=2, lookback=10, rebalance_every=7)
    assert len(result.equity_curve) == 80


def test_run_strategy_default_config() -> None:
    result = run_strategy(_universe())
    assert result.config is not None
    assert len(result.equity_curve) == 80
    assert result.final_equity == result.equity_curve[-1]


def test_run_strategy_inverse_vol() -> None:
    config = StrategyConfig(
        top_n=2,
        lookback=15,
        weighting=WeightingScheme.INVERSE_VOL,
        schedule=RebalanceSchedule.WEEKLY,
    )
    result = run_strategy(_universe(), config)
    assert len(result.equity_curve) == 80
    assert result.rebalances > 0


def test_run_strategy_vol_targeting_runs() -> None:
    config = StrategyConfig(
        top_n=2,
        lookback=15,
        weighting=WeightingScheme.INVERSE_VOL,
        target_vol=0.15,
        schedule=RebalanceSchedule.MONTHLY,
    )
    result = run_strategy(_universe(), config)
    assert len(result.equity_curve) == 80
    metrics = result.metrics()
    assert isinstance(metrics.sharpe, float)


def test_run_strategy_composite_factors() -> None:
    config = StrategyConfig(
        top_n=2,
        lookback=15,
        factor_weights={"momentum": 1.0, "low_vol": 0.5},
    )
    result = run_strategy(_universe(), config)
    assert len(result.equity_curve) == 80


def test_run_strategy_empty_universe() -> None:
    result = run_strategy({})
    assert result.equity_curve == []
    assert result.final_equity == result.starting_equity


def test_result_metrics_uses_config_risk_free() -> None:
    config = StrategyConfig(risk_free=0.02)
    result = run_strategy(_universe(), config)
    # Should not raise and should produce a finite Sharpe.
    assert math.isfinite(result.metrics().sharpe)


def test_monthly_rebalances_fewer_than_weekly() -> None:
    weekly = run_strategy(
        _universe(), StrategyConfig(schedule=RebalanceSchedule.WEEKLY, lookback=10)
    )
    monthly = run_strategy(
        _universe(), StrategyConfig(schedule=RebalanceSchedule.MONTHLY, lookback=10)
    )
    assert monthly.rebalances < weekly.rebalances
