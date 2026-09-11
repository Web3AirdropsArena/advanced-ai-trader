from decimal import Decimal

import httpx
import pytest

from core.config import Settings
from execution.contracts import ExecutionMode, OrderIntent, OrderSide
from execution.jupiter import JupiterClient


@pytest.mark.asyncio
async def test_quote_retries_transient_server_failure() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(
            200,
            request=request,
            json={"outAmount": "1234", "priceImpactPct": "0.12", "routePlan": []},
        )

    client = JupiterClient(
        Settings(),
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    try:
        result = await client.quote(
            OrderIntent(
                asset_id="SOL/USDC",
                input_mint="So11111111111111111111111111111111111111112",
                output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                side=OrderSide.BUY,
                input_amount_atomic=1_000_000,
                notional=Decimal(1),
                max_slippage_bps=50,
                execution_mode=ExecutionMode.RESEARCH,
                decision_id="test",
                guardian_policy_version="guardian-v1",
            )
        )
    finally:
        await client.close()

    assert calls == 2
    assert result.expected_output_atomic == 1234
    assert result.price_impact == Decimal("0.12")
    assert len(result.raw_fingerprint) == 64


@pytest.mark.asyncio
async def test_quote_rejects_malformed_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, json={"routePlan": []})

    client = JupiterClient(
        Settings(),
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    try:
        with pytest.raises(ValueError, match="outAmount"):
            await client.quote(
                OrderIntent(
                    asset_id="SOL/USDC",
                    input_mint="So11111111111111111111111111111111111111112",
                    output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                    side=OrderSide.BUY,
                    input_amount_atomic=1_000_000,
                    notional=Decimal(1),
                    max_slippage_bps=50,
                    execution_mode=ExecutionMode.RESEARCH,
                    decision_id="test",
                    guardian_policy_version="guardian-v1",
                )
            )
    finally:
        await client.close()
