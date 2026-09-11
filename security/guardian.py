from __future__ import annotations

from decimal import Decimal

from core.config import Settings
from core.decision import Decision, DecisionAction, GuardianResult, GuardianVerdict


class Guardian:
    """Independent policy gate between intelligence and execution.

    This component intentionally knows nothing about how a strategy generated
    a proposal. It only evaluates hard policy boundaries and basic uncertainty.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._emergency_stop = False

    def emergency_stop(self) -> None:
        self._emergency_stop = True

    def clear_emergency_stop(self) -> None:
        # Clearing should eventually require a separate operator/auth policy.
        self._emergency_stop = False

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
                policy_version="guardian-v1",
            )

        if current_drawdown >= self.settings.max_portfolio_drawdown:
            return GuardianResult(
                verdict=GuardianVerdict.REJECT,
                reasons=["maximum portfolio drawdown reached"],
                policy_version="guardian-v1",
            )

        if daily_loss >= self.settings.max_daily_loss_fraction:
            return GuardianResult(
                verdict=GuardianVerdict.REJECT,
                reasons=["maximum daily loss reached"],
                policy_version="guardian-v1",
            )

        if decision.action == DecisionAction.NO_TRADE:
            return GuardianResult(
                verdict=GuardianVerdict.HOLD,
                reasons=["decision explicitly requests no trade"],
                policy_version="guardian-v1",
            )

        if decision.uncertainty > 0.80:
            reasons.append("model uncertainty exceeds execution threshold")

        requested = min(decision.target_fraction, self.settings.max_position_fraction)
        if decision.target_fraction > self.settings.max_position_fraction:
            reasons.append("position size capped by immutable policy")

        if decision.uncertainty > 0.80:
            return GuardianResult(
                verdict=GuardianVerdict.HOLD,
                allowed_fraction=Decimal(0),
                reasons=reasons,
                policy_version="guardian-v1",
            )

        if requested <= 0:
            return GuardianResult(
                verdict=GuardianVerdict.REJECT,
                reasons=["requested position size is zero"],
                policy_version="guardian-v1",
            )

        return GuardianResult(
            verdict=GuardianVerdict.REDUCE if reasons else GuardianVerdict.APPROVE,
            allowed_fraction=requested,
            reasons=reasons,
            policy_version="guardian-v1",
        )
