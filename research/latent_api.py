from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_PATH = Path("data/runtime/latent_points.jsonl")


def load_latent_points(path: str | Path = DEFAULT_PATH, limit: int = 30000) -> list[dict[str, Any]]:
    """Load bounded latent telemetry for the command-center API."""
    if limit < 1:
        raise ValueError("limit must be positive")
    source = Path(path)
    if not source.exists():
        return []
    rows = [
        json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    return rows[-limit:]
