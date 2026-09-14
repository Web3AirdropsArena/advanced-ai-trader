from __future__ import annotations

import os
import shutil
import subprocess
from threading import Lock


class ResearchPowerGuard:
    """Hold a systemd idle/sleep inhibitor only while research is active.

    This is intentionally process-scoped: no desktop power settings are changed.
    If systemd-inhibit is unavailable, research continues without pretending that
    suspend prevention is active.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._process: subprocess.Popen[bytes] | None = None
        self.active = False
        self.available = shutil.which("systemd-inhibit") is not None
        self.reason = "Research session active"

    def acquire(self) -> bool:
        with self._lock:
            if self.active and self._process_is_alive():
                return True
            self._stop_locked()
            if not self.available or os.name != "posix":
                self.active = False
                return False
            try:
                self._process = subprocess.Popen(
                    [
                        "systemd-inhibit",
                        "--what=idle:sleep",
                        "--mode=block",
                        "--who=advanced-ai-trader",
                        "--why=" + self.reason,
                        "sleep",
                        "infinity",
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            except (OSError, ValueError):
                self._process = None
                self.active = False
                return False
            self.active = self._process_is_alive()
            if not self.active:
                self._stop_locked()
            return self.active

    def release(self) -> None:
        with self._lock:
            self._stop_locked()

    def status(self) -> dict[str, bool]:
        with self._lock:
            alive = self._process_is_alive()
            if not alive:
                self.active = False
            return {"available": self.available, "active": self.active}

    def _process_is_alive(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def _stop_locked(self) -> None:
        process = self._process
        self._process = None
        self.active = False
        if process is None or process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=1.0)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
                process.wait(timeout=1.0)
            except (OSError, subprocess.TimeoutExpired):
                pass


power_guard = ResearchPowerGuard()
