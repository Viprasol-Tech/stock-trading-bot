"""Example: a multi-factor, risk-parity, vol-targeted rotation backtest.

Run from the repo root with::

    PYTHONPATH=src python examples/factor_rotation.py

Builds a small synthetic universe, blends momentum + low-volatility, sizes the
basket with inverse-volatility (risk parity), targets 15% annual volatility,
rebalances monthly, and prints a full performance report.

Part of Stock Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math

from stock_trading_bot.backtest import run_strategy
from stock_trading_bot.config import RebalanceSchedule, StrategyConfig, WeightingScheme
from stock_trading_bot.report import render_report


def build_universe(n: int = 252) -> dict[str, list[float]]:
    """Five synthetic stocks with distinct drifts and volatilities."""
    specs = {
        "ALPHA": (0.35, 5.0),
        "BETA": (0.12, 3.0),
        "GAMMA": (-0.04, 4.0),
        "DELTA": (0.22, 9.0),
        "OMEGA": (0.03, 2.0),
    }
    return {
        sym: [100.0 + drift * i + vol * math.sin((i + h) / 8.0) for i in range(n)]
        for h, (sym, (drift, vol)) in enumerate(specs.items())
    }


def main() -> None:
    config = StrategyConfig(
        top_n=3,
        lookback=21,
        factor_weights={"momentum": 1.0, "low_vol": 0.5},
        weighting=WeightingScheme.INVERSE_VOL,
        schedule=RebalanceSchedule.MONTHLY,
        target_vol=0.15,
    )
    result = run_strategy(build_universe(), config)
    print(f"Final equity: ${result.final_equity:,.2f}")
    print(f"Total return: {result.total_return_pct:+.2f}%")
    render_report(result)


if __name__ == "__main__":
    main()
