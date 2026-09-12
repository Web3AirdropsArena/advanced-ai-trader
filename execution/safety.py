from __future__ import annotations

from decimal import Decimal

from core.config import Settings
from execution.contracts import ExecutionMode, OrderIntent


class ExecutionPreflight:
    """Reject unsafe execution intents before any venue adapter is called."""

    MAX_SLIPPAGE_BPS = 500

    def __init__(self, settings: Settings):
        self.settings = settings

    def validate(self, order: OrderIntent) -> list[str]:
        errors: list[str] = []

        if order.execution_mode == ExecutionMode.TINY_LIVE:
            errors.append("tiny-live execution is not enabled by the foundation")

        if not order.asset_id.strip():
            errors.append("asset_id must not be empty")

        if not order.decision_id.strip():
            errors.append("decision_id must not be empty")

        if not order.guardian_policy_version.strip():
            errors.append("guardian policy version must not be empty")

        if order.input_amount_atomic <= 0:
            errors.append("input amount must be positive")

        if not order.notional.is_finite() or order.notional <= 0:
            errors.append("notional must be finite and positive")

        if order.max_slippage_bps > self.MAX_SLIPPAGE_BPS:
            errors.append("slippage ceiling exceeds foundation safety limit")

        if order.input_mint.strip() == order.output_mint.strip():
            errors.append("input and output assets must differ")

        if order.notional > Decimal(22) and self.settings.app_env != "production":
            errors.append("development/test environments cannot stage oversized notional")

        return errors
