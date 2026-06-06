"""CLI for Stock Trading Bot.

Subcommands:

* ``demo``     — run a factor-rotation backtest on a synthetic universe.
* ``backtest`` — same engine, fully parameterised (factors, weighting, schedule,
  vol target) with a rich performance report.
* ``rank``     — show the current composite factor ranking of the universe.
* ``version``  — print the installed version.

Part of Stock Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math

import typer
from rich.console import Console
from rich.table import Table

from stock_trading_bot import __version__
from stock_trading_bot.backtest import run_strategy
from stock_trading_bot.config import (
    RebalanceSchedule,
    StrategyConfig,
    WeightingScheme,
)
from stock_trading_bot.factors import rank_by_composite
from stock_trading_bot.report import render_report

app = typer.Typer(add_completion=False, help="Stock Trading Bot - by Viprasol Tech.")
console = Console()


def _universe(n: int = 250) -> dict[str, list[float]]:
    """Synthetic universe: each stock trends at a different rate plus noise."""
    drifts = {"AAA": 0.30, "BBB": 0.10, "CCC": -0.05, "DDD": 0.20, "EEE": 0.02}
    vols = {"AAA": 6.0, "BBB": 3.0, "CCC": 4.0, "DDD": 8.0, "EEE": 2.0}
    return {
        sym: [100.0 + drift * i + vols[sym] * math.sin((i + h) / 9.0) for i in range(n)]
        for h, (sym, drift) in enumerate(drifts.items())
    }


def _parse_factors(spec: str) -> dict[str, float]:
    """Parse ``"momentum=1.0,low_vol=0.5"`` into a weight mapping."""
    weights: dict[str, float] = {}
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        name, _, raw = chunk.partition("=")
        weights[name.strip()] = float(raw) if raw else 1.0
    return weights


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"stock-trading-bot [bold cyan]{__version__}[/] - by Viprasol Tech")


@app.command()
def demo(top_n: int = 2) -> None:
    """Run a factor-rotation backtest on a synthetic stock universe."""
    config = StrategyConfig(top_n=top_n, factor_weights={"momentum": 1.0})
    result = run_strategy(_universe(), config)
    console.print(f"Universe:     5 stocks, hold top {top_n} by momentum")
    console.print(f"Start equity: [bold]${result.starting_equity:,.2f}[/]")
    console.print(f"Final equity: [bold]${result.final_equity:,.2f}[/]")
    console.print(f"Total return: [bold green]{result.total_return_pct:+.2f}%[/]")
    render_report(result, console)


@app.command()
def backtest(
    factors: str = typer.Option(
        "momentum=1.0", help="Comma list of factor=weight (momentum, low_vol, value)."
    ),
    top_n: int = typer.Option(2, min=1, help="Number of names to hold."),
    lookback: int = typer.Option(20, min=2, help="Factor lookback in bars."),
    weighting: WeightingScheme = typer.Option(
        WeightingScheme.EQUAL, help="Position sizing scheme."
    ),
    schedule: RebalanceSchedule = typer.Option(RebalanceSchedule.WEEKLY, help="Rebalance cadence."),
    target_vol: float = typer.Option(0.0, help="Annualized vol target (0 disables vol targeting)."),
) -> None:
    """Run a fully configurable backtest and print a performance report."""
    config = StrategyConfig(
        top_n=top_n,
        lookback=lookback,
        factor_weights=_parse_factors(factors),
        weighting=weighting,
        schedule=schedule,
        target_vol=target_vol if target_vol > 0 else None,
    )
    result = run_strategy(_universe(), config)
    console.print(
        f"Factors: [cyan]{config.factor_weights}[/] | weighting: "
        f"[cyan]{config.weighting.value}[/] | schedule: "
        f"[cyan]{config.schedule.value}[/]"
    )
    render_report(result, console)


@app.command()
def rank(
    factors: str = typer.Option(
        "momentum=1.0", help="Comma list of factor=weight (momentum, low_vol, value)."
    ),
    lookback: int = typer.Option(20, min=2),
    top_n: int = typer.Option(5, min=1),
) -> None:
    """Show the current composite factor ranking of the universe."""
    ranked = rank_by_composite(_universe(), _parse_factors(factors), lookback=lookback)
    table = Table(title="Composite ranking", title_style="bold cyan")
    table.add_column("#", justify="right")
    table.add_column("Symbol", style="bold")
    table.add_column("Score", justify="right")
    for i, (sym, score) in enumerate(ranked[:top_n], start=1):
        table.add_row(str(i), sym, f"{score:+.3f}")
    console.print(table)


if __name__ == "__main__":
    app()
