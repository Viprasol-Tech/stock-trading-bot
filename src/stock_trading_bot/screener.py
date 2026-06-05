"""Cross-sectional momentum screener.

Ranks a universe of stocks by their trailing return and selects the strongest.
"Buy the winners" (cross-sectional momentum) is one of the most studied and
robust equity factors.

Part of Stock Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def momentum(prices: Sequence[float], lookback: int) -> float:
    """Trailing return over ``lookback`` bars (0.0 if not enough history)."""
    if len(prices) <= lookback or prices[-lookback - 1] == 0:
        return 0.0
    return prices[-1] / prices[-lookback - 1] - 1.0


def rank_by_momentum(
    universe: Mapping[str, Sequence[float]],
    lookback: int = 20,
) -> list[tuple[str, float]]:
    """Return ``(symbol, momentum)`` pairs sorted from strongest to weakest."""
    scored = [(sym, momentum(prices, lookback)) for sym, prices in universe.items()]
    return sorted(scored, key=lambda item: item[1], reverse=True)


def select_top(
    universe: Mapping[str, Sequence[float]],
    top_n: int,
    lookback: int = 20,
    min_momentum: float = 0.0,
) -> list[str]:
    """Pick the top ``top_n`` symbols with positive momentum above a floor."""
    ranked = rank_by_momentum(universe, lookback)
    return [sym for sym, score in ranked if score > min_momentum][:top_n]
