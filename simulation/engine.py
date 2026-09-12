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
    """Minimal deterministic buy-side accounting core.

    This is deliberately not a market simulator yet. Each fill is currently
    modeled as a cash outflow; sells, holdings, PnL and mark-to-market are
    intentionally deferred to the full portfolio simulator.
    """

    def run(self, initial_cash: Decimal, fills: list[Fill]) -> SimulationResult:
        if not initial_cash.is_finite() or initial_cash < 0:
            raise ValueError("initial_cash must be finite and non-negative")

        cash = initial_cash
        fees = Decimal(0)
        slippage = Decimal(0)
        for fill in fills:
            values = (fill.price, fill.quantity, fill.fee, fill.slippage)
            if any(not value.is_finite() for value in values):
                raise ValueError("fills cannot contain non-finite values")
            if fill.quantity <= 0 or fill.price <= 0 or fill.fee < 0 or fill.slippage < 0:
                raise ValueError("fills must have positive price/quantity and non-negative costs")

            notional = fill.price * fill.quantity
            total_cost = notional + fill.fee + fill.slippage
            if total_cost > cash:
                raise ValueError("simulation cannot spend more cash than is available")

            cash -= total_cost
            fees += fill.fee
            slippage += fill.slippage

        return SimulationResult(
            initial_cash=initial_cash,
            final_cash=cash,
            total_fees=fees,
            total_slippage=slippage,
            trades=len(fills),
        )
