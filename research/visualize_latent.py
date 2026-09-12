from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px


DEFAULT_INPUT = Path("data/runtime/latent_points.jsonl")
DEFAULT_OUTPUT = Path("visualizations/latent_space.html")


def render_latent_space(
    input_path: str | Path = DEFAULT_INPUT,
    output_path: str | Path = DEFAULT_OUTPUT,
) -> Path:
    """Render bounded latent snapshots as an interactive 3D HTML animation."""
    source = Path(input_path)
    destination = Path(output_path)
    if not source.exists():
        raise FileNotFoundError(f"Latent telemetry not found: {source}")

    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("Latent telemetry contains no points.")

    frame = pd.DataFrame(rows)
    frame["epoch"] = frame["epoch"].astype(int)
    frame["pnl_or_return"] = frame["pnl_or_return"].astype(float)
    frame["hover"] = (
        "epoch=" + frame["epoch"].astype(str)
        + "<br>pred=" + frame["predicted_class"].astype(str)
        + "<br>true=" + frame["true_label"].astype(str)
        + "<br>return=" + frame["pnl_or_return"].round(6).astype(str)
    )

    figure = px.scatter_3d(
        frame,
        x="x",
        y="y",
        z="z",
        color="predicted_class",
        symbol="true_label",
        size="pnl_or_return",
        animation_frame="epoch",
        hover_name="hover",
        title="Advanced AI Trader — 3D latent representation evolution",
    )
    figure.update_traces(marker={"sizemin": 3, "sizeref": 2})
    figure.update_layout(scene={"xaxis_title": "PC1", "yaxis_title": "PC2", "zaxis_title": "PC3"})

    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(destination, include_plotlyjs="cdn")
    return destination


if __name__ == "__main__":
    print(render_latent_space())
