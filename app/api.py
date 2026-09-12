from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from core.config import Settings
from research.supervisor import supervisor


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    if settings.trading_mode == "research":
        supervisor.start()
    try:
        yield
    finally:
        supervisor.stop()


app = FastAPI(title="Advanced AI Trader", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    settings = Settings()
    return {"status": "ready", "trading_mode": settings.trading_mode}


@app.get("/api/v1/system")
def system() -> dict[str, str]:
    settings = Settings()
    return {
        "environment": settings.app_env,
        "trading_mode": settings.trading_mode,
        "guardian": "enabled",
        "live_execution": "disabled_until_explicit_enablement",
    }


@app.get("/api/v1/research/status")
def research_status() -> dict[str, object]:
    """Return live training telemetry from the research supervisor."""
    return supervisor.status()
