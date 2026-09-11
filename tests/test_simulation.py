from decimal import Decimal

from simulation.engine import Fill, PortfolioSimulator


def test_simulator_accounts_for_fees_and_slippage() -> None:
    result = PortfolioSimulator().run(
        Decimal(22),
        [
            Fill(
                price=Decimal("10"),
                quantity=Decimal(1),
                fee=Decimal("0.10"),
                slippage=Decimal("0.05"),
            )
        ],
    )
    assert result.final_cash == Decimal("11.85")
    assert result.total_fees == Decimal("0.10")
    assert result.total_slippage == Decimal("0.05")
    assert result.trades == 1
