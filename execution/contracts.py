from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class ExecutionMode(StrEnum):
    RESEARCH = "research"
    PAPER = "paper"
    SHADOW = "shadow"
    TINY_LIVE = "tiny_live"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderIntent(BaseModel):
    asset_id: str
    input_mint: str
    output_mint: str
    side: OrderSide
    input_amount_atomic: int = Field(gt=0)
    notional: Decimal = Field(gt=0)
    max_slippage_bps: int = Field(gt=0)
    execution_mode: ExecutionMode = ExecutionMode.RESEARCH
    decision_id: str
    guardian_policy_version: str


class ExecutionQuote(BaseModel):
    venue: str
    input_amount_atomic: int = Field(gt=0)
    expected_output_atomic: int = Field(ge=0)
    price_impact: Decimal = Field(ge=0)
    route_summary: str
    raw_fingerprint: str


class RouteCandidate(BaseModel):
    venue: str
    route_id: str
    expected_out: Decimal = Field(ge=0)
    estimated_fee: Decimal = Field(ge=0)
    estimated_slippage_bps: Decimal = Field(ge=0)
    estimated_latency_ms: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)


class ExecutionPlan(BaseModel):
    order: OrderIntent
    routes: list[RouteCandidate]
    selected_route_id: str | None = None
    rationale: str
