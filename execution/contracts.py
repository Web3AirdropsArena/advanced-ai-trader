from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, FiniteFloat


class ExecutionMode(StrEnum):
    RESEARCH = "research"
    PAPER = "paper"
    SHADOW = "shadow"
    TINY_LIVE = "tiny_live"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderIntent(BaseModel):
    asset_id: str = Field(min_length=1, max_length=128)
    input_mint: str = Field(min_length=1, max_length=64)
    output_mint: str = Field(min_length=1, max_length=64)
    side: OrderSide
    input_amount_atomic: int = Field(gt=0)
    notional: Decimal = Field(gt=0)
    max_slippage_bps: int = Field(gt=0, le=500)
    execution_mode: ExecutionMode = ExecutionMode.RESEARCH
    decision_id: str = Field(min_length=1, max_length=128)
    guardian_policy_version: str = Field(min_length=1, max_length=128)


class ExecutionQuote(BaseModel):
    venue: str = Field(min_length=1, max_length=128)
    input_amount_atomic: int = Field(gt=0)
    expected_output_atomic: int = Field(ge=0)
    price_impact: Decimal | None = Field(default=None, ge=0)
    route_summary: str = Field(max_length=4000)
    raw_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class RouteCandidate(BaseModel):
    venue: str = Field(min_length=1, max_length=128)
    route_id: str = Field(min_length=1, max_length=256)
    expected_out: Decimal = Field(ge=0)
    estimated_fee: Decimal = Field(ge=0)
    estimated_slippage_bps: Decimal = Field(ge=0)
    estimated_latency_ms: FiniteFloat = Field(ge=0)
    confidence: FiniteFloat = Field(ge=0, le=1)


class ExecutionPlan(BaseModel):
    order: OrderIntent
    routes: list[RouteCandidate] = Field(default_factory=list, max_length=100)
    selected_route_id: str | None = None
    rationale: str = Field(min_length=1, max_length=4000)
