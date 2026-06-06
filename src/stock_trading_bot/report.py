"""Render a backtest into a human-readable performance report.

Produces a rich table of headline metrics plus a compact ASCII sparkline of the
equity curve, so a run can be eyeballed straight from the terminal.

Part of Stock Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence

from rich.console import Console
from rich.table import Table

from stock_trading_bot.backtest import BacktestResult

_SPARK_CHARS = "_.-=+*#%@"


def sparkline(values: Sequence[float], width: int = 48) -> str:
    """Compact ASCII sparkline of a series, downsampled to ``width`` points."""
    if not values:
        return ""
    if len(values) > width:
        step = len(values) / width
        sampled = [values[min(int(i * step), len(values) - 1)] for i in range(width)]
    else:
        sampled = list(values)
    lo, hi = min(sampled), max(sampled)
    span = hi - lo
    if span == 0:
        return _SPARK_CHARS[0] * len(sampled)
    out = []
    last = len(_SPARK_CHARS) - 1
    for v in sampled:
        idx = int((v - lo) / span * last)
        out.append(_SPARK_CHARS[idx])
    return "".join(out)


def metrics_table(result: BacktestResult) -> Table:
    """Build a rich table of headline performance metrics."""
    m = result.metrics()
    table = Table(title="Performance Report", title_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    rows = [
        ("Starting equity", f"${result.starting_equity:,.2f}"),
        ("Final equity", f"${result.final_equity:,.2f}"),
        ("Total return", f"{m.total_return * 100:+.2f}%"),
        ("CAGR", f"{m.cagr * 100:+.2f}%"),
        ("Volatility (ann.)", f"{m.volatility * 100:.2f}%"),
        ("Sharpe", f"{m.sharpe:.2f}"),
        ("Sortino", f"{m.sortino:.2f}"),
        ("Max drawdown", f"{m.max_drawdown * 100:.2f}%"),
        ("Calmar", f"{m.calmar:.2f}"),
        ("Win rate", f"{m.win_rate * 100:.1f}%"),
        ("Rebalances", str(result.rebalances)),
    ]
    for name, value in rows:
        table.add_row(name, value)
    return table


def render_report(result: BacktestResult, console: Console | None = None) -> None:
    """Print the metrics table and an equity-curve sparkline."""
    console = console or Console()
    console.print(metrics_table(result))
    spark = sparkline(result.equity_curve)
    if spark:
        console.print(f"Equity curve: [green]{spark}[/]")
