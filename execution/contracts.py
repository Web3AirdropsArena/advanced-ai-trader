from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel, Field


class ExecutionMode(StrEnum):
    RESEARCH = "research"
    PAPER = "paper"
    SHADOW = "shadow"
    TINY_LIVE = "tiny_live"


class OrderIntent(BaseModel):
    asset_id: str
    side: str
    notional: Decimal = Field(gt=0)
    max_slippage_bps: Decimal = Field(gt=0)
    execution_mode: ExecutionMode = ExecutionMode.RESEARCH
    decision_id: str
    guardian_policy_version: str


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
