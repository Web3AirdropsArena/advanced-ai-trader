from __future__ import annotations

from decimal import Decimal

from core.config import Settings
from execution.contracts import ExecutionMode, OrderIntent


class ExecutionPreflight:
    """Reject unsafe execution intents before any venue adapter is called."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def validate(self, order: OrderIntent) -> list[str]:
        errors: list[str] = []

        if order.execution_mode == ExecutionMode.TINY_LIVE:
            errors.append("tiny-live execution is not enabled by the foundation")

        if order.notional <= 0:
            errors.append("notional must be positive")

        if order.max_slippage_bps > 500:
            errors.append("slippage ceiling exceeds foundation safety limit")

        if order.input_mint == order.output_mint:
            errors.append("input and output assets must differ")

        if order.notional > Decimal("22") and self.settings.app_env != "production":
            errors.append("development/test environments cannot stage oversized notional")

        return errors
