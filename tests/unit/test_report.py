"""Tests for the report rendering helpers."""

from __future__ import annotations

from stock_trading_bot.backtest import run_strategy
from stock_trading_bot.config import StrategyConfig
from stock_trading_bot.report import metrics_table, render_report, sparkline


def test_sparkline_empty() -> None:
    assert sparkline([]) == ""


def test_sparkline_flat_series() -> None:
    spark = sparkline([100.0] * 10)
    assert len(spark) == 10
    assert len(set(spark)) == 1  # all same char


def test_sparkline_downsamples_to_width() -> None:
    spark = sparkline(list(range(1000)), width=40)
    assert len(spark) == 40


def test_sparkline_rising_series_ends_high() -> None:
    spark = sparkline(list(range(50)), width=50)
    # last point is the max -> last char is the top of the ramp
    assert spark[-1] == "@"
    assert spark[0] == "_"


def test_metrics_table_has_rows() -> None:
    result = run_strategy(
        {"A": [100 + i for i in range(60)], "B": [100 - i for i in range(60)]},
        StrategyConfig(lookback=10),
    )
    table = metrics_table(result)
    assert table.row_count >= 10


def test_render_report_runs(capsys) -> None:
    result = run_strategy(
        {"A": [100 + i for i in range(60)], "B": [100 - i for i in range(60)]},
        StrategyConfig(lookback=10),
    )
    render_report(result)
    out = capsys.readouterr().out
    assert "Performance Report" in out
    assert "Sharpe" in out
