from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_INPUT = Path("data/runtime/latent_points.jsonl")
DEFAULT_OUTPUT = Path("visualizations/latent_space.html")


HTML_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Advanced AI Trader — 3D Latent Space</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script></head>
<body><div id="latent" style="width:100vw;height:100vh"></div>
<script>
const rows = __ROWS__;
const epochs = [...new Set(rows.map(r => r.epoch))].sort((a,b) => a-b);
const frameFor = epoch => rows.filter(r => r.epoch === epoch);
const traceFor = epoch => { const r=frameFor(epoch); return [{x:r.map(p=>p.x),y:r.map(p=>p.y),z:r.map(p=>p.z),mode:'markers',type:'scatter3d',text:r.map(p=>`pred=${p.predicted_class}<br>true=${p.true_label}<br>return=${p.pnl_or_return}`),hoverinfo:'text',marker:{size:4}}]; };
const frames = epochs.map(e => ({name:String(e),data:traceFor(e)}));
Plotly.newPlot('latent', traceFor(epochs[epochs.length-1]), {title:'Advanced AI Trader — 3D latent representation evolution',scene:{xaxis_title:'PC1',yaxis_title:'PC2',zaxis_title:'PC3'},updatemenus:[{type:'buttons',buttons:[{label:'▶ Play',method:'animate',args:[null,{frame:{duration:450,redraw:true},fromcurrent:true}]},{label:'⏸ Pause',method:'animate',args:[[null],{frame:{duration:0,redraw:false},mode:'immediate'}]}]}],sliders:[{currentvalue:{prefix:'Epoch: '},steps:epochs.map(e=>({label:String(e),method:'animate',args:[[String(e)],{mode:'immediate',frame:{duration:250,redraw:true},transition:{duration:0}}]}))}]}, {responsive:true}).then(()=>Plotly.addFrames('latent',frames));
</script></body></html>"""


def render_latent_space(input_path: str | Path = DEFAULT_INPUT, output_path: str | Path = DEFAULT_OUTPUT) -> Path:
    """Render latent snapshots as a dependency-free interactive 3D HTML page."""
    source = Path(input_path)
    destination = Path(output_path)
    if not source.exists():
        raise FileNotFoundError(f"Latent telemetry not found: {source}")
    rows: list[dict[str, Any]] = [
        json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if not rows:
        raise ValueError("Latent telemetry contains no points.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(HTML_TEMPLATE.replace("__ROWS__", json.dumps(rows)), encoding="utf-8")
    return destination


if __name__ == "__main__":
    print(render_latent_space())
