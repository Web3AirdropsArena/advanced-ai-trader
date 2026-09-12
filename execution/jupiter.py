from __future__ import annotations

import asyncio
import hashlib
from decimal import Decimal
from typing import Any

import httpx

from core.config import Settings
from execution.contracts import ExecutionQuote, OrderIntent, OrderSide


class JupiterClient:
    """Read-only Jupiter Swap V2 integration for research and paper execution.

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
        if self.settings.jupiter_api_key is None:
            raise RuntimeError("JUPITER_API_KEY is required for Jupiter Swap V2")

        params = {
            "inputMint": intent.input_mint,
            "outputMint": intent.output_mint,
            "amount": str(intent.input_amount_atomic),
        }
        response = await self._get_with_retry(
            f"{self.settings.jupiter_api_base}/order",
            params=params,
            headers={"x-api-key": self.settings.jupiter_api_key.get_secret_value()},
        )
        try:
            payload: dict[str, Any] = response.json()
        except ValueError as exc:
            raise ValueError("Jupiter order returned invalid JSON") from exc

        required_fields = ("outAmount", "router", "requestId")
        missing_fields = [field for field in required_fields if field not in payload]
        if missing_fields:
            raise ValueError(
                "Jupiter order is missing required response fields: "
                + ", ".join(missing_fields)
            )

        try:
            out_amount = int(payload["outAmount"])
            router = str(payload["router"])
            request_id = str(payload["requestId"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Jupiter order returned invalid required response fields") from exc
        if out_amount < 0 or not router or not request_id:
            raise ValueError("Jupiter order returned invalid response fields")

        # Swap V2 does not expose the legacy priceImpactPct field used by the
        # old endpoint. Keep the value explicitly unknown rather than inventing 0.
        route_summary = f"router={router};request_id={request_id}"
        return ExecutionQuote(
            venue="jupiter",
            input_amount_atomic=int(intent.input_amount_atomic),
            expected_output_atomic=out_amount,
            price_impact=None,
            route_summary=route_summary,
            raw_fingerprint=hashlib.sha256(response.content).hexdigest(),
        )

    async def _get_with_retry(
        self,
        url: str,
        *,
        params: dict[str, str],
        headers: dict[str, str],
    ) -> httpx.Response:
        """GET with bounded retry for transient transport, throttling and server failures."""
        for attempt in range(self._MAX_ATTEMPTS):
            try:
                response = await self._client.get(url, params=params, headers=headers)
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
