from __future__ import annotations

from decimal import Decimal
from typing import Any

import httpx

from core.config import Settings
from execution.contracts import ExecutionQuote, OrderIntent


class JupiterClient:
    """Read-only Jupiter integration for research and paper execution.

    This adapter deliberately does not sign or submit transactions. Live
    transaction submission belongs behind a separate credential-isolated
    execution process and Guardian authorization.
    """

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self.settings = settings
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def quote(self, intent: OrderIntent) -> ExecutionQuote:
        if intent.side != "buy":
            raise NotImplementedError("initial adapter supports quote construction for buys only")

        params = {
            "inputMint": intent.input_mint,
            "outputMint": intent.output_mint,
            "amount": str(intent.input_amount_atomic),
            "slippageBps": str(intent.max_slippage_bps),
        }
        response = await self._client.get(f"{self.settings.jupiter_api_base}/swap/v1/quote", params=params)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()

        out_amount = Decimal(str(payload["outAmount"]))
        return ExecutionQuote(
            venue="jupiter",
            input_amount_atomic=int(intent.input_amount_atomic),
            expected_output_atomic=int(out_amount),
            price_impact=Decimal(str(payload.get("priceImpactPct", "0"))),
            route_summary=str(payload.get("routePlan", [])),
            raw_fingerprint=str(hash(response.text)),
        )
