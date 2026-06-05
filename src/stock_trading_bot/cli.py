"""CLI for Stock Trading Bot.

``stock-trading-bot demo`` runs a top-N momentum rotation across a synthetic
universe of stocks and reports the result.

Part of Stock Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math

import typer
from rich.console import Console

from stock_trading_bot import __version__
from stock_trading_bot.backtest import run_backtest

app = typer.Typer(add_completion=False, help="Stock Trading Bot — by Viprasol Tech.")
console = Console()


def _universe(n: int = 250) -> dict[str, list[float]]:
    """Synthetic universe: each stock trends at a different rate plus noise."""
    drifts = {"AAA": 0.30, "BBB": 0.10, "CCC": -0.05, "DDD": 0.20, "EEE": 0.02}
    return {
        sym: [100.0 + drift * i + 5.0 * math.sin((i + h) / 9.0) for i in range(n)]
        for h, (sym, drift) in enumerate(drifts.items())
    }


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"stock-trading-bot [bold cyan]{__version__}[/] — by Viprasol Tech")


@app.command()
def demo(top_n: int = 2) -> None:
    """Run a momentum-rotation backtest on a synthetic stock universe."""
    result = run_backtest(_universe(), top_n=top_n)
    console.print(f"Universe:     5 stocks, hold top {top_n} by momentum")
    console.print(f"Start equity: [bold]${result.starting_equity:,.2f}[/]")
    console.print(f"Final equity: [bold]${result.final_equity:,.2f}[/]")
    console.print(f"Total return: [bold green]{result.total_return_pct:+.2f}%[/]")


if __name__ == "__main__":
    app()
