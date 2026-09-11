from __future__ import annotations

import asyncio
import hashlib
from decimal import Decimal
from typing import Any

import httpx

from core.config import Settings
from execution.contracts import ExecutionQuote, OrderIntent, OrderSide


class JupiterClient:
    """Read-only Jupiter integration for research and paper execution.

    This adapter deliberately does not sign or submit transactions. Live
    transaction submission belongs behind a separate credential-isolated
    execution process and Guardian authorization.
    """

    _MAX_ATTEMPTS = 3

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self.settings = settings
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def quote(self, intent: OrderIntent) -> ExecutionQuote:
        if intent.side != OrderSide.BUY:
            raise NotImplementedError("initial adapter supports quote construction for buys only")

        params = {
            "inputMint": intent.input_mint,
            "outputMint": intent.output_mint,
            "amount": str(intent.input_amount_atomic),
            "slippageBps": str(intent.max_slippage_bps),
        }
        response = await self._get_with_retry(
            f"{self.settings.jupiter_api_base}/swap/v1/quote", params=params
        )
        payload: dict[str, Any] = response.json()

        try:
            out_amount = int(payload["outAmount"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Jupiter quote is missing a valid outAmount") from exc
        if out_amount < 0:
            raise ValueError("Jupiter quote returned a negative outAmount")

        try:
            price_impact = Decimal(str(payload.get("priceImpactPct", "0")))
        except (ArithmeticError, ValueError) as exc:
            raise ValueError("Jupiter quote returned an invalid price impact") from exc
        if price_impact < 0:
            raise ValueError("Jupiter quote returned a negative price impact")

        return ExecutionQuote(
            venue="jupiter",
            input_amount_atomic=int(intent.input_amount_atomic),
            expected_output_atomic=out_amount,
            price_impact=price_impact,
            route_summary=str(payload.get("routePlan", [])),
            raw_fingerprint=hashlib.sha256(response.content).hexdigest(),
        )

    async def _get_with_retry(self, url: str, *, params: dict[str, str]) -> httpx.Response:
        """GET with bounded retry for transient transport, throttling and server failures."""
        for attempt in range(self._MAX_ATTEMPTS):
            try:
                response = await self._client.get(url, params=params)
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError):
                if attempt == self._MAX_ATTEMPTS - 1:
                    raise
                await asyncio.sleep(2**attempt)
                continue

            if response.status_code == 429 or response.status_code >= 500:
                if attempt == self._MAX_ATTEMPTS - 1:
                    response.raise_for_status()
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = min(float(retry_after), 10.0) if retry_after is not None else 2**attempt
                except ValueError:
                    delay = 2**attempt
                await asyncio.sleep(delay)
                continue

            response.raise_for_status()
            return response

        raise RuntimeError("unreachable retry state")
