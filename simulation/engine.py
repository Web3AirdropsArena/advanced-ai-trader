from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Fill:
    price: Decimal
    quantity: Decimal
    fee: Decimal = Decimal(0)
    slippage: Decimal = Decimal(0)


@dataclass(frozen=True)
class SimulationResult:
    initial_cash: Decimal
    final_cash: Decimal
    total_fees: Decimal
    total_slippage: Decimal
    trades: int


class PortfolioSimulator:
    """Minimal deterministic accounting core.

    This is deliberately not a market simulator yet. Microstructure, DEX
    routing, latency and adversarial liquidity will be layered on top of it.
    """

    def run(self, initial_cash: Decimal, fills: list[Fill]) -> SimulationResult:
        if initial_cash < 0:
            raise ValueError("initial_cash cannot be negative")

        cash = initial_cash
        fees = Decimal(0)
        slippage = Decimal(0)
        for fill in fills:
            if fill.quantity < 0 or fill.price < 0 or fill.fee < 0 or fill.slippage < 0:
                raise ValueError("fills cannot contain negative values")
            notional = fill.price * fill.quantity
            cash -= notional + fill.fee + fill.slippage
            fees += fill.fee
            slippage += fill.slippage

        return SimulationResult(
            initial_cash=initial_cash,
            final_cash=cash,
            total_fees=fees,
            total_slippage=slippage,
            trades=len(fills),
        )
