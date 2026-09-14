from __future__ import annotations

import os
import sys
import time
from threading import Lock
from typing import Any


class ResearchTerminalUI:
    """TTY-friendly research console with persistent logs and animated progress."""

    _RESET = "\033[0m"
    _BOLD = "\033[1m"
    _DIM = "\033[2m"
    _CYAN = "\033[36m"
    _BLUE = "\033[34m"
    _GREEN = "\033[32m"
    _YELLOW = "\033[33m"
    _MAGENTA = "\033[35m"
    _RED = "\033[31m"
    _WHITE = "\033[97m"

    def __init__(self) -> None:
        self.enabled = sys.stdout.isatty() and os.getenv("NO_COLOR") is None
        self._lock = Lock()
        self._spinner = 0
        self._last_epoch = 0
        self._started = time.monotonic()

    def _paint(self, color: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"{color}{text}{self._RESET}"

    def banner(self) -> None:
        with self._lock:
            print()
            print(self._paint(self._CYAN, "╔══════════════════════════════════════════════════════════════════════╗"))
            print(self._paint(self._CYAN, "║  ADVANCED AI TRADER  •  RESEARCH COMMAND CENTER                    ║"))
            print(self._paint(self._CYAN, "╠══════════════════════════════════════════════════════════════════════╣"))
            print(self._paint(self._WHITE, "║  MODE       : RESEARCH (SAFE / NO LIVE EXECUTION)                  ║"))
            print(self._paint(self._WHITE, "║  ENGINE     : benchmark learning + latent representation lab      ║"))
            print(self._paint(self._WHITE, "║  CONSOLE    : live telemetry / persistent event log               ║"))
            print(self._paint(self._CYAN, "╚══════════════════════════════════════════════════════════════════════╝"))
            print()
            print(self._paint(self._DIM, "Live research logs will appear below. Each event is kept on its own line."))

    def event(self, event_type: str, message: str, **details: Any) -> None:
        with self._lock:
            timestamp = time.strftime("%H:%M:%S")
            label = event_type.upper().replace("_", " ")
            color = self._GREEN if "start" in event_type or "complete" in event_type else self._CYAN
            if "stop" in event_type or "error" in event_type:
                color = self._RED
            suffix = ""
            if details:
                rendered = " ".join(f"{key}={value}" for key, value in details.items())
                suffix = f" {self._paint(self._DIM, rendered)}"
            print(f"{self._paint(self._DIM, timestamp)} {self._paint(color, '[' + label + ']')} {message}{suffix}", flush=True)

    def progress(self, state: dict[str, Any]) -> None:
        epoch = int(state.get("epoch") or 0)
        epochs = max(int(state.get("epochs") or 1), 1)
        progress = float(state.get("progress") or 0.0)
        if epoch == self._last_epoch and progress < 100.0:
            return
        self._last_epoch = epoch
        width = 44
        filled = max(0, min(width, int(width * progress / 100.0)))
        bar = "█" * filled + "░" * (width - filled)
        self._spinner = (self._spinner + 1) % 4
        spinner = "|/-\\"[self._spinner]
        loss = state.get("validation_loss")
        loss_text = "n/a" if loss is None else f"{float(loss):.6f}"
        elapsed = time.monotonic() - self._started
        print()
        print(self._paint(self._BLUE, "┌─ TRAINING TELEMETRY ────────────────────────────────────────────────┐"))
        print(self._paint(self._WHITE, f"│ {spinner} Epoch {epoch:>2}/{epochs:<2}  [{bar}] {progress:6.2f}%"))
        print(self._paint(self._WHITE, f"│ Samples: {int(state.get('samples_processed') or 0):>7,}   Validation loss: {loss_text:<12}  Latent points: {int(state.get('latent_points') or 0):>5,}"))
        print(self._paint(self._WHITE, f"│ Stage: {str(state.get('stage') or 'idle'):<34} Elapsed: {elapsed:7.1f}s"))
        print(self._paint(self._BLUE, "└─────────────────────────────────────────────────────────────────────┘"), flush=True)


terminal_ui = ResearchTerminalUI()
