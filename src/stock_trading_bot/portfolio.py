"""A simple multi-symbol paper portfolio with equal-weight rebalancing.

Holds cash plus share quantities per symbol, and can rebalance to an equal-weight
target basket at current prices — the execution side of a momentum-rotation bot.

Part of Stock Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence


class Portfolio:
    """Cash + per-symbol share holdings, valued at supplied prices."""

    def __init__(self, cash: float = 100_000.0) -> None:
        self.cash = cash
        self.shares: dict[str, float] = {}

    def value(self, prices: Mapping[str, float]) -> float:
        """Total portfolio value (cash + holdings) at the given prices."""
        holdings = sum(qty * prices.get(sym, 0.0) for sym, qty in self.shares.items())
        return self.cash + holdings

    def rebalance(self, targets: Sequence[str], prices: Mapping[str, float]) -> None:
        """Rebalance to an equal-weight basket of ``targets``.

        Sells everything not in the target set, then equal-weights the rest using
        the latest prices. A no-op (goes fully to cash) when ``targets`` is empty.
        """
        # 1. Liquidate positions no longer wanted.
        for sym in list(self.shares):
            if sym not in targets and self.shares[sym] > 0:
                self.cash += self.shares[sym] * prices.get(sym, 0.0)
                self.shares[sym] = 0.0

        if not targets:
            return

        weights = {sym: 1.0 / len(targets) for sym in targets}
        self.rebalance_weighted(weights, prices)

    def rebalance_weighted(
        self,
        weights: Mapping[str, float],
        prices: Mapping[str, float],
    ) -> None:
        """Rebalance to arbitrary target weights of current equity.

        ``weights`` maps symbol -> fraction of equity to hold (need not sum to
        1.0; a sum below 1.0 leaves the remainder in cash, enabling volatility
        targeting / de-risking). Symbols absent from ``weights`` are liquidated.
        """
        for sym in list(self.shares):
            if sym not in weights and self.shares[sym] > 0:
                self.cash += self.shares[sym] * prices.get(sym, 0.0)
                self.shares[sym] = 0.0

        if not weights:
            return

        equity = self.value(prices)
        for sym, weight in weights.items():
            price = prices.get(sym, 0.0)
            if price <= 0:
                continue
            desired_shares = (equity * weight) / price
            current = self.shares.get(sym, 0.0)
            self.cash -= (desired_shares - current) * price
            self.shares[sym] = desired_shares
