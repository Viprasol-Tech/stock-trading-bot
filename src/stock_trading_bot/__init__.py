"""Stock Trading Bot — AI factor-rotation stock bot by Viprasol Tech.

A small, dependency-light quant toolkit: blend equity factors (momentum,
low-volatility, value), size positions with equal-weight or inverse-volatility
risk parity, target portfolio volatility, and backtest the whole thing with a
full performance report.
"""

from __future__ import annotations

from stock_trading_bot.backtest import BacktestResult, run_backtest, run_strategy
from stock_trading_bot.config import (
    RebalanceSchedule,
    StrategyConfig,
    WeightingScheme,
)
from stock_trading_bot.factors import (
    composite_scores,
    low_volatility,
    momentum,
    rank_by_composite,
    select_top_composite,
    value,
    volatility,
)
from stock_trading_bot.metrics import PerformanceReport, performance_report
from stock_trading_bot.portfolio import Portfolio
from stock_trading_bot.screener import rank_by_momentum, select_top

__version__ = "0.2.0"
__author__ = "Viprasol Tech Private Limited"
__all__ = [
    "BacktestResult",
    "PerformanceReport",
    "Portfolio",
    "RebalanceSchedule",
    "StrategyConfig",
    "WeightingScheme",
    "__version__",
    "composite_scores",
    "low_volatility",
    "momentum",
    "performance_report",
    "rank_by_composite",
    "rank_by_momentum",
    "run_backtest",
    "run_strategy",
    "select_top",
    "select_top_composite",
    "value",
    "volatility",
]
