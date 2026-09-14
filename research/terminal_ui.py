from __future__ import annotations

import os
import shutil
import sys
import time
from threading import Lock
from typing import Any


class ResearchTerminalUI:
    """Responsive, TTY-only research command center for the Zero Book 15."""

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
        self._logs: list[tuple[str, str, str]] = []
        self._last_render = 0.0

    def _paint(self, color: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"{color}{text}{self._RESET}"

    @staticmethod
    def _width() -> int:
        return max(80, min(shutil.get_terminal_size((120, 30)).columns, 140))

    @staticmethod
    def _bar(value: float, width: int) -> str:
        value = max(0.0, min(100.0, value))
        filled = int(width * value / 100.0)
        return "█" * filled + "░" * (width - filled)

    def banner(self) -> None:
        with self._lock:
            self._state = {
                "status": "starting", "stage": "stage_1_research", "progress": 0.0,
                "epoch": 0, "epochs": 0, "validation_loss": None,
                "samples_processed": 0, "latent_points": 0,
            }
            self._logs.clear()
            self._logs.append((time.strftime("%H:%M:%S"), "SYSTEM", "Research command center initialized"))
            self._render_locked()

    def event(self, event_type: str, message: str, **details: Any) -> None:
        with self._lock:
            timestamp = time.strftime("%H:%M:%S")
            label = event_type.upper().replace("_", " ")
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
            detail_text = ""
            if details:
                rendered = " ".join(f"{key}={value}" for key, value in details.items())
                detail_text = f" {self._paint(self._DIM, rendered)}"
            self._logs.append((timestamp, label, f"{message}{detail_text}"))
            self._logs = self._logs[-500:]
            self._render_locked(event_color=color)

    def progress(self, state: dict[str, Any]) -> None:
        with self._lock:
            self._state = dict(state)
            self._spinner = (self._spinner + 1) % 4
            self._render_locked()

    def _render_locked(self, event_color: str | None = None) -> None:
        if not sys.stdout.isatty():
            return
        now = time.monotonic()
        if now - self._last_render < 0.03 and event_color is None:
            return
        self._last_render = now
        width = self._width()
        inner = width - 4
        progress = float(self._state.get("progress") or 0.0)
        epoch = int(self._state.get("epoch") or 0)
        epochs = max(int(self._state.get("epochs") or 1), 1)
        loss = self._state.get("validation_loss")
        loss_text = "n/a" if loss is None else f"{float(loss):.4f}"
        samples = int(self._state.get("samples_processed") or 0)
        latent = int(self._state.get("latent_points") or 0)
        elapsed = time.monotonic() - self._started
        hours = elapsed / 3600.0
        days = hours / 24.0
        cpu = self._state.get("cpu_percent")
        memory = self._state.get("memory_percent")
        speed = self._state.get("training_speed")
        speed_text = "n/a" if speed is None else f"{float(speed):.2f}/s"
        cpu_text = "n/a" if cpu is None else f"{float(cpu):.0f}%"
        mem_text = "n/a" if memory is None else f"{float(memory):.0f}%"
        spin = "|/-\\"[self._spinner]

        lines: list[str] = []
        def add(text: str = "") -> None:
            lines.append(text[:width])

        border = "─" * inner
        add(self._paint(self._CYAN, f"╭{border}╮"))
        add(self._paint(self._BOLD + self._CYAN, "│ ⚡ ADVANCED AI TRADER  ::  AUTONOMOUS RESEARCH CORE".ljust(width - 1) + "│"))
        add(self._paint(self._WHITE, f"│ 🧪 RESEARCH │ {self._status_icon()} {str(self._state.get('status') or 'IDLE').upper()} │ 🛡 GUARDIAN ARMED │ 🔴 LIVE OFF │ ⏱ {self._duration(elapsed)}".ljust(width - 1) + "│"))
        add(self._paint(self._CYAN, f"├{border}┤"))

        overall = progress
        add(self._paint(self._WHITE, f"│ PROJECT  [{self._bar(overall, 24)}] {overall:5.1f}% │ PHASE {progress:5.1f}% │ CPU {cpu_text:>4} │ RAM {mem_text:>4} │ ACTIVE {hours:6.1f}h / {days:5.2f}d".ljust(width - 1) + "│"))
        add(self._paint(self._WHITE, f"│ SPEED {speed_text:>9} │ EPOCH {epoch:>2}/{epochs:<2} │ LOSS {loss_text:>8} │ ETA {self._eta_text(progress, elapsed):>8} │ LATENT {latent:>5,}".ljust(width - 1) + "│"))
        add(self._paint(self._CYAN, f"├{border}┤"))

        roadmap = "✓ Research" if self._state.get("stage_one_complete") else "◉ Research"
        statuses = "[COMPLETED]" if self._state.get("stage_one_complete") else "[CURRENT]"
        add(self._paint(self._WHITE, f"│ ROADMAP  {roadmap} {statuses} │ → Historical Training [NEXT] │ ○ Walk-Forward │ ○ Stress │ ○ Paper │ ○ Shadow".ljust(width - 1) + "│"))
        add(self._paint(self._DIM, "│          ○ Tiny-Live │ ○ Validation │ ○ Adaptive-Live  |  next-stage gate: validation evidence".ljust(width - 1) + "│"))
        add(self._paint(self._CYAN, f"├{border}┤"))

        pulse = self._pulse_frame()
        signal = self._signal_frame()
        add(self._paint(self._GREEN, f"│ 🪙 MARKET PULSE  {pulse}".ljust(width // 2) + self._paint(self._MAGENTA, f"🧠 AI SIGNAL FIELD  {signal}").ljust(width - width // 2 - 1) + "│"))
        add(self._paint(self._DIM, "│ benchmark mode: market feed not connected; pulse is visual-only │ AI field: research activity, not a trading signal".ljust(width - 1) + "│"))
        add(self._paint(self._CYAN, f"├{border}┤"))

        train_bar = self._bar(progress, max(20, inner - 50))
        add(self._paint(self._BLUE, f"│ 🧠 TRAINING  E{epoch}/{epochs} [{train_bar}] {progress:5.1f}% │ Loss {loss_text} │ Speed {speed_text} │ Samples {samples:,} │ ETA {self._eta_text(progress, elapsed)}".ljust(width - 1) + "│"))
        add(self._paint(self._CYAN, f"├{border}┤"))
        add(self._paint(self._WHITE, "│ LIVE EVENT STREAM".ljust(width - 1) + "│"))

        log_rows = max(4, shutil.get_terminal_size((120, 30)).lines - len(lines) - 3)
        recent = self._logs[-log_rows:]
        for timestamp, label, message in recent:
            prefix = f"│ {timestamp} {label:<14} "
            available = max(10, width - len(prefix) - 1)
            add(prefix + message[:available].ljust(available) + "│")
        while len(lines) < shutil.get_terminal_size((120, 30)).lines - 1:
            add("│".ljust(width - 1) + "│")
        add(self._paint(self._DIM, f"│ {spin} Research active...   [P]ause [R]esume [S]tatus [L]ogs [Q]uit".ljust(width - 1) + "│"))
        add(self._paint(self._CYAN, f"╰{border}╯"))

        sys.stdout.write("\033[2J\033[H" + "\n".join(lines) + "\033[H")
        sys.stdout.flush()

    def _status_icon(self) -> str:
        status = str(self._state.get("status") or "").lower()
        if status in {"training", "starting"}:
            return "🟢"
        if status in {"completed"}:
            return "✓"
        if status in {"stopped"}:
            return "⏸"
        return "⚪"

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

    def _pulse_frame(self) -> str:
        frames = ("▁▂▃▄▅▆▇█", "▂▃▄▅▆▇█▇", "▃▄▅▆▇█▇▆", "▄▅▆▇█▇▆▅")
        return frames[self._spinner]

    def _signal_frame(self) -> str:
        frames = ("·   ◉   ·", " ·  ◉  · ", "  · ◉ ·  ", " ·  ◉  · ")
        return frames[self._spinner]


terminal_ui = ResearchTerminalUI()
