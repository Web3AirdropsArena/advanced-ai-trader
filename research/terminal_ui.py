from __future__ import annotations

import os
import shutil
import sys
import time
from threading import Lock
from typing import Any


class ResearchTerminalUI:
    """Bounded TTY research console with stable-width rendering."""

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
        self._started = time.monotonic()
        self._state: dict[str, Any] = {}
        self._logs: list[tuple[str, str, str, str]] = []
        self._last_render = 0.0

    def _paint(self, color: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"{color}{text}{self._RESET}"

    @staticmethod
    def _terminal() -> tuple[int, int]:
        size = shutil.get_terminal_size((120, 30))
        return max(88, min(size.columns, 140)), max(20, size.lines)

    @staticmethod
    def _fit(text: str, width: int) -> str:
        return text[:width].ljust(width)

    @staticmethod
    def _bar(value: float, width: int) -> str:
        value = max(0.0, min(100.0, value))
        filled = int(round(width * value / 100.0))
        return "█" * filled + "░" * (width - filled)

    def _row(self, text: str, width: int, color: str | None = None) -> str:
        content = self._fit(text, width - 2)
        rendered = f"│ {content} │"
        return self._paint(color, rendered) if color else rendered

    def banner(self) -> None:
        with self._lock:
            self._started = time.monotonic()
            self._spinner = 0
            self._state = {
                "status": "starting",
                "stage": "stage_1_research",
                "progress": 0.0,
                "research_progress": 0.0,
                "epoch": 0,
                "epochs": 0,
                "validation_loss": None,
                "samples_processed": 0,
                "latent_points": 0,
                "program_stage_index": 1,
                "program_stage_count": 4,
                "program_stage_name": "Benchmark Research",
                "model_id": "mlp-benchmark",
            }
            self._logs.clear()
            self._logs.append(
                (time.strftime("%H:%M:%S"), "SYSTEM", "Research command center initialized", "system")
            )
            self._render_locked()

    def event(self, event_type: str, message: str, **details: Any) -> None:
        with self._lock:
            timestamp = time.strftime("%H:%M:%S")
            label = event_type.upper().replace("_", " ")
            data_kind = str(details.get("data_kind") or "")
            if data_kind:
                label = f"DATA/{data_kind.upper()}"
            if "error" in event_type or "stop" in event_type:
                color = self._RED
            elif "complete" in event_type or "start" in event_type:
                color = self._GREEN
            elif "latent" in event_type or "model" in event_type:
                color = self._MAGENTA
            elif "evaluation" in event_type or "warning" in event_type:
                color = self._YELLOW
            else:
                color = self._BLUE
            detail_items = [
                f"{key}={value}"
                for key, value in details.items()
                if key != "data_kind"
            ]
            detail_text = f" {' '.join(detail_items)}" if detail_items else ""
            self._logs.append((timestamp, label, f"{message}{detail_text}", color))
            self._logs = self._logs[-500:]
            self._render_locked()

    def progress(self, state: dict[str, Any]) -> None:
        with self._lock:
            self._state = dict(state)
            self._spinner = (self._spinner + 1) % 4
            self._render_locked()

    def _render_locked(self) -> None:
        if not sys.stdout.isatty():
            return
        now = time.monotonic()
        if now - self._last_render < 0.03:
            return
        self._last_render = now
        width, height = self._terminal()
        inner = width - 2
        elapsed = time.monotonic() - self._started
        status = str(self._state.get("status") or "IDLE").upper()
        stage = str(self._state.get("program_stage_name") or "Benchmark Research")
        stage_index = int(self._state.get("program_stage_index") or 1)
        stage_count = int(self._state.get("program_stage_count") or 4)
        total = float(self._state.get("research_progress") or 0.0)
        phase = float(self._state.get("progress") or 0.0)
        epoch = int(self._state.get("epoch") or 0)
        epochs = max(int(self._state.get("epochs") or 1), 1)
        loss = self._state.get("validation_loss")
        loss_text = "n/a" if loss is None else f"{float(loss):.5f}"
        samples = int(self._state.get("samples_processed") or 0)
        latent = int(self._state.get("latent_points") or 0)
        cpu = self._state.get("cpu_percent")
        memory = self._state.get("memory_percent")
        speed = self._state.get("training_speed")
        cpu_text = "n/a" if cpu is None else f"{float(cpu):.0f}%"
        mem_text = "n/a" if memory is None else f"{float(memory):.0f}%"
        speed_text = "n/a" if speed is None else f"{float(speed):.1f}/s"
        model = str(self._state.get("model_id") or "n/a")
        guard = self._state.get("power_guard") or {}
        guard_text = "ON" if guard.get("active") else "OFF"
        spin = "|/-\\"[self._spinner]

        lines: list[tuple[str, str | None]] = []
        border = "─" * inner
        lines.append((f"╭{border}╮", self._CYAN))
        lines.append((
            self._fit("│ ADVANCED AI TRADER :: AUTONOMOUS RESEARCH CORE │", width),
            self._BOLD + self._CYAN,
        ))
        lines.append((
            self._row(
                f"RESEARCH  {status:<10} | GUARDIAN {guard_text:<3} | LIVE EXECUTION OFF | RUNTIME {self._duration(elapsed)}",
                width,
            ),
            self._WHITE,
        ))
        lines.append((f"├{border}┤", self._CYAN))

        lines.append((
            self._row(
                f"RESEARCH PROGRAM  [{self._bar(total, 32)}] {total:5.1f}%  |  STAGE {stage_index}/{stage_count}  {stage}",
                width,
            ),
            self._GREEN,
        ))
        lines.append((
            self._row(
                f"STAGE PROGRESS    [{self._bar(phase, 32)}] {phase:5.1f}%  |  EPOCH {epoch:02d}/{epochs:02d}  |  LOSS {loss_text:>8}  |  ETA {self._eta_text(phase, elapsed)}",
                width,
            ),
            self._BLUE,
        ))
        lines.append((
            self._row(
                f"RESOURCES  CPU {cpu_text:>4} | RAM {mem_text:>4} | SPEED {speed_text:>7} | SAMPLES {samples:,} | LATENT {latent:,}",
                width,
            ),
            self._WHITE,
        ))
        lines.append((f"├{border}┤", self._CYAN))

        roadmap = "1 Benchmark -> 2 Historical -> 3 Walk-Forward -> 4 Stress/Robustness"
        lines.append((self._row(f"RESEARCH ROADMAP  {roadmap}", width), self._WHITE))
        lines.append((
            self._row(
                "Research progress is weighted across research phases; stage progress is NOT the total research progress.",
                width,
            ),
            self._DIM,
        ))
        lines.append((f"├{border}┤", self._CYAN))

        field = (
            f"AI RESEARCH FIELD  | model={model} | latent=3D | points={latent:,} | "
            f"loss={loss_text} | state={status}"
        )
        lines.append((self._row(field, width), self._MAGENTA))
        lines.append((
            self._row(
                "Purpose: monitor learned representation health; this is NOT a market/trading signal.",
                width,
            ),
            self._DIM,
        ))
        lines.append((
            self._row(
                "DATA ACTIVITY  | benchmark=synthetic/local | external market feed=OFF | retrieval is shown in event labels when a real source is active",
                width,
            ),
            self._YELLOW,
        ))
        lines.append((f"├{border}┤", self._CYAN))
        lines.append((self._row("LIVE EVENT STREAM", width), self._WHITE))

        footer = self._row(
            f"{spin} Research active  [P]ause [R]esume [S]tatus [L]ogs [Q]uit  |  {self._state.get('message', '')}",
            width,
        )
        fixed_rows = len(lines) + 1
        available_logs = max(2, height - fixed_rows - 1)
        for timestamp, label, message, color in self._logs[-available_logs:]:
            prefix = f"{timestamp} {label:<18} "
            available = max(10, inner - len(prefix) - 2)
            lines.append((self._row(prefix + message[:available], width), color))

        while len(lines) < height - 1:
            lines.append((self._row("", width), None))
        lines = lines[: height - 2]
        lines.append((footer, self._DIM))
        lines.append((f"╰{border}╯", self._CYAN))

        output = "\033[2J\033[H" + "\n".join(
            self._paint(color, text) if color else text for text, color in lines
        )
        sys.stdout.write(output)
        sys.stdout.flush()

    @staticmethod
    def _duration(seconds: float) -> str:
        total = max(0, int(seconds))
        days, rem = divmod(total, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)
        return f"{days}d {hours:02d}h {minutes:02d}m {secs:02d}s"

    @staticmethod
    def _eta_text(progress: float, elapsed: float) -> str:
        if progress <= 0.0 or elapsed <= 0.0 or progress >= 100.0:
            return "--:--"
        remaining = elapsed * (100.0 - progress) / progress
        minutes, seconds = divmod(int(remaining), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


terminal_ui = ResearchTerminalUI()
