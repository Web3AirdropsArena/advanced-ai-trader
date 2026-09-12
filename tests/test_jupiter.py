from decimal import Decimal

import httpx
import pytest
from pydantic import SecretStr

from core.config import Settings
from execution.contracts import ExecutionMode, OrderIntent, OrderSide
from execution.jupiter import JupiterClient


def test_settings_requires_https_for_jupiter() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        Settings(jupiter_api_base="http://example.test/swap/v2")


@pytest.mark.asyncio
async def test_quote_retries_transient_server_failure() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.headers["x-api-key"] == "test-key"
        assert request.url.path == "/swap/v2/order"
        if calls == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(
            200,
            request=request,
            json={"outAmount": "1234", "router": "metis", "requestId": "req-1"},
        )

    client = JupiterClient(
        Settings(jupiter_api_key=SecretStr("test-key")),
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    try:
        result = await client.quote(
            OrderIntent(
                asset_id="SOL/USDC",
                input_mint="So11111111111111111111111111111111111111112",
                output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGkZwyTDt1v",
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
    assert result.price_impact is None
    assert result.route_summary == "router=metis;request_id=req-1"
    assert len(result.raw_fingerprint) == 64


@pytest.mark.asyncio
async def test_quote_rejects_malformed_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            json={"router": "metis", "requestId": "req-1"},
        )

    client = JupiterClient(
        Settings(jupiter_api_key=SecretStr("test-key")),
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    try:
        with pytest.raises(ValueError, match="outAmount"):
            await client.quote(
                OrderIntent(
                    asset_id="SOL/USDC",
                    input_mint="So11111111111111111111111111111111111111112",
                    output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGkZwyTDt1v",
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


@pytest.mark.asyncio
async def test_quote_requires_api_key() -> None:
    # Explicitly override .env so this test remains deterministic on developer machines.
    client = JupiterClient(
        Settings(jupiter_api_key=None),
        httpx.AsyncClient(transport=httpx.MockTransport(lambda r: None)),
    )
    try:
        with pytest.raises(RuntimeError, match="JUPITER_API_KEY"):
            await client.quote(
                OrderIntent(
                    asset_id="SOL/USDC",
                    input_mint="So11111111111111111111111111111111111111112",
                    output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGkZwyTDt1v",
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
