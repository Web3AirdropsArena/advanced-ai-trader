from __future__ import annotations

import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from core.config import Settings
from research.dashboard import DASHBOARD_HTML
from research.latent_api import load_latent_points
from research.latent_supervisor import supervisor

_process_started = time.monotonic()
_process_cpu_started = os.times()
_prev_cpu_times = os.times()
_prev_cpu_wall = time.monotonic()


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


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return DASHBOARD_HTML


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD_HTML


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
        "web_dashboard": "enabled",
    }


@app.get("/api/v1/research/status")
def research_status() -> dict[str, object]:
    return supervisor.status()


@app.get("/api/v1/research/latent")
def research_latent() -> dict[str, object]:
    points = load_latent_points()
    return {"dimensions": 3, "count": len(points), "points": points}


@app.get("/api/v1/research/history")
def research_history(limit: int = 20) -> list[dict[str, object]]:
    return supervisor.history(limit=limit)


@app.get("/api/v1/research/events")
def research_events(limit: int = 500) -> list[dict[str, object]]:
    return supervisor.events(limit=limit)


@app.get("/api/v1/research/agents")
def research_agents() -> list[dict[str, str]]:
    return [
        {"name": "Researcher", "role": "experiment orchestration", "status": "ready"},
        {"name": "Math Scientist", "role": "hypothesis / objective critique", "status": "ready"},
        {"name": "Feature Scientist", "role": "feature quality / leakage review", "status": "ready"},
        {"name": "Model Builder", "role": "candidate architecture lab", "status": "ready"},
        {"name": "Adversarial Critic", "role": "stress and failure analysis", "status": "ready"},
        {"name": "Evaluator", "role": "out-of-sample evidence", "status": "ready"},
    ]


@app.get("/api/v1/research/resources")
def research_resources() -> dict[str, object]:
    global _prev_cpu_times, _prev_cpu_wall
    rss_mb = None
    try:
        with open("/proc/self/status", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("VmRSS:"):
                    rss_mb = round(float(line.split()[1]) / 1024, 2)
                    break
    except (OSError, ValueError):
        pass
    ram_total_mb = None
    ram_available_mb = None
    try:
        memory = {}
        with open("/proc/meminfo", encoding="utf-8") as handle:
            for line in handle:
                key, value = line.split(":", 1)
                memory[key] = float(value.split()[0]) / 1024
        ram_total_mb = round(memory.get("MemTotal", 0.0), 2)
        ram_available_mb = round(memory.get("MemAvailable", 0.0), 2)
    except (OSError, ValueError):
        pass
    ram_used_mb = None
    ram_percent = None
    if ram_total_mb and ram_available_mb is not None:
        ram_used_mb = round(ram_total_mb - ram_available_mb, 2)
        ram_percent = round((ram_used_mb / ram_total_mb) * 100.0, 2)
    load_1m = None
    try:
        load_1m = round(os.getloadavg()[0], 2)
    except OSError:
        pass
    now = time.monotonic()
    current_cpu_times = os.times()
    wall_delta = max(now - _prev_cpu_wall, 1e-6)
    process_delta = (
        current_cpu_times.user
        + current_cpu_times.system
        - _prev_cpu_times.user
        - _prev_cpu_times.system
    )
    process_cpu_percent = round(min(100.0, max(0.0, process_delta / wall_delta * 100.0)), 2)
    _prev_cpu_times = current_cpu_times
    _prev_cpu_wall = now
    elapsed = max(now - _process_started, 0.001)
    cpu = os.times()
    started_cpu = _process_cpu_started
    cpu_seconds = round((cpu.user - started_cpu.user) + (cpu.system - started_cpu.system), 3)
    status = supervisor.status()
    return {
        "rss_mb": rss_mb,
        "ram_total_mb": ram_total_mb,
        "ram_available_mb": ram_available_mb,
        "ram_used_mb": ram_used_mb,
        "ram_percent": ram_percent,
        "process_cpu_percent": process_cpu_percent,
        "load_1m": load_1m,
        "cpu_seconds_since_start": cpu_seconds,
        "process_uptime_seconds": round(elapsed, 1),
        "worker": "running" if status["status"] in {"training", "completed"} else "stopped",
    }


@app.post("/api/v1/research/control")
def research_control(action: str) -> dict[str, object]:
    if action == "start":
        supervisor.start()
    elif action == "stop":
        supervisor.stop()
    else:
        raise HTTPException(status_code=400, detail="action must be start or stop")
    return supervisor.status()
