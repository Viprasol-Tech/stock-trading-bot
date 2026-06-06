"""Tests for the Typer CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from stock_trading_bot import __version__
from stock_trading_bot.cli import _parse_factors, app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_demo_command() -> None:
    result = runner.invoke(app, ["demo", "--top-n", "2"])
    assert result.exit_code == 0
    assert "Total return" in result.stdout
    assert "Performance Report" in result.stdout


def test_backtest_command_with_factors() -> None:
    result = runner.invoke(
        app,
        [
            "backtest",
            "--factors",
            "momentum=1.0,low_vol=0.5",
            "--weighting",
            "inverse_vol",
            "--schedule",
            "monthly",
            "--target-vol",
            "0.15",
        ],
    )
    assert result.exit_code == 0
    assert "Performance Report" in result.stdout


def test_rank_command() -> None:
    result = runner.invoke(app, ["rank", "--top-n", "3"])
    assert result.exit_code == 0
    assert "Composite ranking" in result.stdout


def test_parse_factors_basic() -> None:
    assert _parse_factors("momentum=1.0,low_vol=0.5") == {
        "momentum": 1.0,
        "low_vol": 0.5,
    }


def test_parse_factors_defaults_weight_to_one() -> None:
    assert _parse_factors("momentum") == {"momentum": 1.0}


def test_backtest_rejects_unknown_factor() -> None:
    result = runner.invoke(app, ["backtest", "--factors", "bogus=1.0"])
    assert result.exit_code != 0
