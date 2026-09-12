from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from core.config import Settings
from research.latent_api import load_latent_points
from research.latent_supervisor import supervisor


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
    """Return live training and latent-space telemetry."""
    return supervisor.status()


@app.get("/api/v1/research/latent")
def research_latent() -> dict[str, object]:
    """Return recent 3D latent points for the command-center graph."""
    points = load_latent_points()
    return {"dimensions": 3, "count": len(points), "points": points}


@app.get("/research/latent", response_class=HTMLResponse)
def latent_dashboard() -> str:
    """Serve a lightweight live 3D latent-space command-center view."""
    return """<!doctype html><html><head><meta charset='utf-8'><title>AI Latent Space</title>
<script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script></head><body>
<div id='graph' style='width:100vw;height:92vh'></div><pre id='status'>Connecting…</pre>
<script>
async function refresh(){
 const [s,l]=await Promise.all([fetch('/api/v1/research/status'),fetch('/api/v1/research/latent')]);
 const state=await s.json(), payload=await l.json();
 document.getElementById('status').textContent=`${state.status} | ${state.stage} | experiment=${state.experiment_id} | epoch=${state.epoch}/${state.epochs} | progress=${state.progress}% | latent points=${payload.count} | heartbeat=${state.heartbeat_at}`;
 const p=payload.points;
 Plotly.react('graph',[{x:p.map(v=>v.x),y:p.map(v=>v.y),z:p.map(v=>v.z),mode:'markers',type:'scatter3d',text:p.map(v=>`epoch=${v.epoch}<br>pred=${v.predicted_class}<br>true=${v.true_label}<br>return=${v.pnl_or_return}`),hoverinfo:'text',marker:{size:4}}],{title:'Advanced AI Trader — live 3D latent representation',scene:{xaxis_title:'PC1',yaxis_title:'PC2',zaxis_title:'PC3'}} ,{responsive:true});
}
refresh(); setInterval(refresh,2000);
</script></body></html>"""
