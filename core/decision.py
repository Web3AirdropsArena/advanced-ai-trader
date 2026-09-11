from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel, Field


class DecisionAction(StrEnum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    NO_TRADE = "no_trade"


class Decision(BaseModel):
    """A model proposal, not an execution authorization."""

    action: DecisionAction
    confidence: float = Field(ge=0, le=1)
    target_fraction: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    rationale: str
    model_version: str
    uncertainty: float = Field(ge=0, le=1)


class GuardianVerdict(StrEnum):
    APPROVE = "approve"
    REDUCE = "reduce"
    HOLD = "hold"
    REJECT = "reject"
    EMERGENCY_STOP = "emergency_stop"


class GuardianResult(BaseModel):
    verdict: GuardianVerdict
    allowed_fraction: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    policy_version: str
