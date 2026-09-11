from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, FiniteFloat


class DecisionAction(StrEnum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    NO_TRADE = "no_trade"


class Decision(BaseModel):
    """A model proposal, not an execution authorization."""

    action: DecisionAction
    confidence: FiniteFloat = Field(ge=0, le=1)
    target_fraction: Decimal = Field(default=Decimal(0), ge=0, le=1)
    rationale: str = Field(min_length=1, max_length=4000)
    model_version: str = Field(min_length=1, max_length=256)
    uncertainty: FiniteFloat = Field(ge=0, le=1)
