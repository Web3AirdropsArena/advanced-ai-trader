from decimal import Decimal

from core.config import Settings
from execution.contracts import ExecutionMode, OrderIntent, OrderSide
from execution.safety import ExecutionPreflight


def order(**changes) -> OrderIntent:
    values = {
        "asset_id": "SOL/USDC",
        "input_mint": "So11111111111111111111111111111111111111112",
        "output_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "side": OrderSide.BUY,
        "input_amount_atomic": 1_000_000,
        "notional": Decimal(1),
        "max_slippage_bps": 50,
        "execution_mode": ExecutionMode.RESEARCH,
        "decision_id": "decision-test",
        "guardian_policy_version": "guardian-v1",
    }
    values.update(changes)
    return OrderIntent(**values)


def test_tiny_live_is_blocked() -> None:
    errors = ExecutionPreflight(Settings()).validate(order(execution_mode=ExecutionMode.TINY_LIVE))
    assert any("tiny-live" in error for error in errors)


def test_excessive_slippage_is_blocked() -> None:
    errors = ExecutionPreflight(Settings()).validate(order(max_slippage_bps=501))
    assert any("slippage" in error for error in errors)


def test_identical_assets_are_blocked() -> None:
    errors = ExecutionPreflight(Settings()).validate(
        order(output_mint="So11111111111111111111111111111111111111112")
    )
    assert any("assets" in error for error in errors)
