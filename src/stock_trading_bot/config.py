"""Typed strategy configuration via pydantic.

:class:`StrategyConfig` is the single source of truth for a backtest run:
which factors to blend, how to size positions, how often to rebalance, and the
volatility-target / risk settings. It validates inputs up front so the engine
never has to second-guess its parameters.

Part of Stock Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class WeightingScheme(str, Enum):
    """How selected symbols are turned into position weights."""

    EQUAL = "equal"
    INVERSE_VOL = "inverse_vol"


class RebalanceSchedule(str, Enum):
    """How often the portfolio rotates into freshly ranked winners."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

    @property
    def bars(self) -> int:
        """Approximate number of trading bars between rebalances."""
        return {"daily": 1, "weekly": 5, "monthly": 21}[self.value]


class StrategyConfig(BaseModel):
    """Validated parameters for a factor-rotation backtest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    top_n: int = Field(default=3, ge=1, description="Number of names to hold.")
    lookback: int = Field(default=20, ge=2, description="Factor lookback in bars.")
    starting_cash: float = Field(default=100_000.0, gt=0)

    factor_weights: dict[str, float] = Field(
        default_factory=lambda: {"momentum": 1.0},
        description="Blend of factor name -> weight (e.g. momentum/low_vol/value).",
    )
    weighting: WeightingScheme = WeightingScheme.EQUAL
    schedule: RebalanceSchedule = RebalanceSchedule.WEEKLY

    min_score: float = Field(default=0.0, description="Composite score floor to hold.")

    target_vol: float | None = Field(
        default=None,
        gt=0,
        description="Annualized vol target; enables vol targeting when set.",
    )
    max_leverage: float = Field(default=2.0, gt=0, le=5.0)
    risk_free: float = Field(default=0.0, ge=0, description="Annual risk-free rate.")

    @field_validator("factor_weights")
    @classmethod
    def _validate_factors(cls, value: dict[str, float]) -> dict[str, float]:
        from stock_trading_bot.factors import FACTOR_FUNCS

        if not value:
            raise ValueError("factor_weights must contain at least one factor")
        unknown = set(value) - set(FACTOR_FUNCS)
        if unknown:
            raise ValueError(
                f"unknown factors {sorted(unknown)}; choose from {sorted(FACTOR_FUNCS)}"
            )
        if all(w == 0 for w in value.values()):
            raise ValueError("at least one factor weight must be non-zero")
        return value

    @model_validator(mode="after")
    def _check_rebalance(self) -> StrategyConfig:
        # top_n must be reachable in principle; this is a sanity guard only.
        if self.top_n < 1:  # pragma: no cover - covered by Field ge
            raise ValueError("top_n must be >= 1")
        return self

    @property
    def rebalance_every(self) -> int:
        """Bars between rebalances, from the chosen schedule."""
        return self.schedule.bars
