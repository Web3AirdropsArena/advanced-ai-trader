from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel, Field


class DataKind(StrEnum):
    TRADE = "trade"
    QUOTE = "quote"
    CANDLE = "candle"
    ORDER_BOOK = "order_book"
    ONCHAIN = "onchain"
    TOKEN_METADATA = "token_metadata"
    SOCIAL = "social"
    NEWS = "news"
    EVENT = "event"


class DataQuality(StrEnum):
    VERIFIED = "verified"
    ACCEPTABLE = "acceptable"
    DEGRADED = "degraded"
    QUARANTINED = "quarantined"


class Observation(BaseModel):
    asset_id: str
    kind: DataKind
    observed_at: datetime
    received_at: datetime
    source: str
    sequence: int | None = None
    payload: dict[str, object]
    quality: DataQuality = DataQuality.ACCEPTABLE
    source_reliability: float = Field(default=1.0, ge=0, le=1)


class DataQualityReport(BaseModel):
    accepted: bool
    quality: DataQuality
    reliability: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    checked_at: datetime
    source: str


class PricePoint(BaseModel):
    asset_id: str
    timestamp: datetime
    price: Decimal = Field(gt=0)
    volume: Decimal = Field(default=Decimal("0"), ge=0)
    source: str
    quality: DataQuality
