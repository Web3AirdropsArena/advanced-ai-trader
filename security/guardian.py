from __future__ import annotations

from decimal import Decimal

from core.config import Settings
from core.decision import Decision, DecisionAction, GuardianResult, GuardianVerdict


class Guardian:
    """Independent policy gate between intelligence and execution.

    This component intentionally knows nothing about how a strategy generated
    a proposal. It only evaluates hard policy boundaries and basic uncertainty.
    Emergency-stop recovery is intentionally not exposed here; a future
    authenticated operator control plane must perform that action.
    """

    POLICY_VERSION = "guardian-v1"
    UNCERTAINTY_HOLD_THRESHOLD = 0.80

    def __init__(self, settings: Settings):
        self.settings = settings
        self._emergency_stop = False

    def emergency_stop(self) -> None:
        """Latch the emergency stop until an external recovery policy clears it."""
        self._emergency_stop = True

    def evaluate(
        self,
        decision: Decision,
        *,
        current_drawdown: Decimal = Decimal(0),
        daily_loss: Decimal = Decimal(0),
    ) -> GuardianResult:
        reasons: list[str] = []

        if self._emergency_stop:
            return GuardianResult(
                verdict=GuardianVerdict.EMERGENCY_STOP,
                reasons=["emergency stop is active"],
                policy_version=self.POLICY_VERSION,
            )

        telemetry_error = self._validate_telemetry(current_drawdown, daily_loss)
        if telemetry_error is not None:
            return GuardianResult(
                verdict=GuardianVerdict.REJECT,
                reasons=[telemetry_error],
                policy_version=self.POLICY_VERSION,
            )

        if current_drawdown >= self.settings.max_portfolio_drawdown:
            return GuardianResult(
                verdict=GuardianVerdict.REJECT,
                reasons=["maximum portfolio drawdown reached"],
                policy_version=self.POLICY_VERSION,
            )

        if daily_loss >= self.settings.max_daily_loss_fraction:
            return GuardianResult(
                verdict=GuardianVerdict.REJECT,
                reasons=["maximum daily loss reached"],
                policy_version=self.POLICY_VERSION,
            )

        if decision.action == DecisionAction.NO_TRADE:
            return GuardianResult(
                verdict=GuardianVerdict.HOLD,
                reasons=["decision explicitly requests no trade"],
                policy_version=self.POLICY_VERSION,
            )

        if decision.uncertainty > self.UNCERTAINTY_HOLD_THRESHOLD:
            return GuardianResult(
                verdict=GuardianVerdict.HOLD,
                reasons=["model uncertainty exceeds execution threshold"],
                policy_version=self.POLICY_VERSION,
            )

        requested = min(decision.target_fraction, self.settings.max_position_fraction)
        if decision.target_fraction > self.settings.max_position_fraction:
            reasons.append("position size capped by immutable policy")

        if requested <= 0:
            return GuardianResult(
                verdict=GuardianVerdict.REJECT,
                reasons=["requested position size is zero"],
                policy_version=self.POLICY_VERSION,
            )

        return GuardianResult(
            verdict=GuardianVerdict.REDUCE if reasons else GuardianVerdict.APPROVE,
            allowed_fraction=requested,
            reasons=reasons,
            policy_version=self.POLICY_VERSION,
        )

    @staticmethod
    def _validate_telemetry(current_drawdown: Decimal, daily_loss: Decimal) -> str | None:
        for name, value in (("current drawdown", current_drawdown), ("daily loss", daily_loss)):
            if not value.is_finite():
                return f"{name} telemetry is non-finite"
            if value < 0:
                return f"{name} telemetry cannot be negative"
        return None
