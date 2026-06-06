"""Tests for the pydantic StrategyConfig."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from stock_trading_bot.config import (
    RebalanceSchedule,
    StrategyConfig,
    WeightingScheme,
)


def test_defaults_are_sane() -> None:
    config = StrategyConfig()
    assert config.top_n == 3
    assert config.factor_weights == {"momentum": 1.0}
    assert config.weighting is WeightingScheme.EQUAL
    assert config.schedule is RebalanceSchedule.WEEKLY


def test_schedule_bars_mapping() -> None:
    assert RebalanceSchedule.DAILY.bars == 1
    assert RebalanceSchedule.WEEKLY.bars == 5
    assert RebalanceSchedule.MONTHLY.bars == 21


def test_rebalance_every_property() -> None:
    config = StrategyConfig(schedule=RebalanceSchedule.MONTHLY)
    assert config.rebalance_every == 21


def test_rejects_unknown_factor() -> None:
    with pytest.raises(ValidationError):
        StrategyConfig(factor_weights={"nope": 1.0})


def test_rejects_empty_factors() -> None:
    with pytest.raises(ValidationError):
        StrategyConfig(factor_weights={})


def test_rejects_all_zero_weights() -> None:
    with pytest.raises(ValidationError):
        StrategyConfig(factor_weights={"momentum": 0.0})


def test_rejects_bad_top_n() -> None:
    with pytest.raises(ValidationError):
        StrategyConfig(top_n=0)


def test_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        StrategyConfig(unknown_field=1)  # type: ignore[call-arg]


def test_is_frozen() -> None:
    config = StrategyConfig()
    with pytest.raises(ValidationError):
        config.top_n = 5  # type: ignore[misc]


def test_target_vol_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        StrategyConfig(target_vol=0.0)
    assert StrategyConfig(target_vol=0.15).target_vol == 0.15
