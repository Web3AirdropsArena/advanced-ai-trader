from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class TokenCandidate(BaseModel):
    mint: str
    symbol: str
    decimals: int = Field(ge=0, le=18)
    verified: bool = False
    liquidity_usd: Decimal = Field(ge=0)
    volume_24h_usd: Decimal = Field(ge=0)
    holder_count: int = Field(ge=0)
    mint_authority_active: bool = False
    freeze_authority_active: bool = False
    source_count: int = Field(ge=0)


class TokenGateResult(BaseModel):
    eligible: bool
    score: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)


class TokenSafetyGate:
    """Hard pre-trade screening; discovery does not imply eligibility."""

    def __init__(self, min_liquidity_usd: Decimal = Decimal(5000)):
        self.min_liquidity_usd = min_liquidity_usd

    def evaluate(self, token: TokenCandidate) -> TokenGateResult:
        reasons: list[str] = []
        if token.liquidity_usd < self.min_liquidity_usd:
            reasons.append("insufficient liquidity")
        if token.mint_authority_active:
            reasons.append("mint authority remains active")
        if token.freeze_authority_active:
            reasons.append("freeze authority remains active")
        if token.holder_count < 50:
            reasons.append("holder distribution is too concentrated for foundation policy")
        if token.source_count < 2:
            reasons.append("insufficient independent source corroboration")

        score = 1.0
        score -= min(
            0.35,
            float(max(Decimal(0), self.min_liquidity_usd - token.liquidity_usd) / self.min_liquidity_usd),
        )
        score -= 0.20 if token.mint_authority_active else 0
        score -= 0.20 if token.freeze_authority_active else 0
        score -= 0.15 if token.holder_count < 50 else 0
        score -= 0.10 if token.source_count < 2 else 0
        score = max(0.0, min(1.0, score))

        return TokenGateResult(eligible=not reasons, score=score, reasons=reasons)
