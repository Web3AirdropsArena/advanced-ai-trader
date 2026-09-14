from __future__ import annotations

import ctypes
import os
import shutil
import signal
import subprocess
from threading import Lock
from typing import Any, cast


class ResearchPowerGuard:
    """Hold a systemd idle/sleep inhibitor only while research is active."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._process: subprocess.Popen[bytes] | None = None
        self.active = False
        self.available = os.name == "posix" and shutil.which("systemd-inhibit") is not None
        self.reason = "Research session active"

    def acquire(self) -> bool:
        with self._lock:
            if self.active and self._process_is_alive():
                return True
            self._stop_locked()
            if not self.available:
                return False
            try:
                kwargs: dict[str, Any] = {
                    "stdin": subprocess.DEVNULL,
                    "stdout": subprocess.DEVNULL,
                    "stderr": subprocess.DEVNULL,
                }
                if sys_platform_linux():
                    kwargs["preexec_fn"] = _kill_child_when_parent_dies
                self._process = subprocess.Popen(
                    ["systemd-inhibit", "--what=idle:sleep", "--mode=block",
                     "--who=advanced-ai-trader", "--why=" + self.reason, "sleep", "infinity"],
                    **kwargs,
                )
            except (OSError, ValueError):
                self._process = None
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
            self.active = self._process_is_alive()
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


def sys_platform_linux() -> bool:
    return os.name == "posix" and os.uname().sysname.lower() == "linux"


def _kill_child_when_parent_dies() -> None:
    """Linux child hook: terminate the inhibitor if the Python parent dies."""
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    prctl = cast(Any, libc.prctl)
    if prctl(1, signal.SIGTERM) != 0:  # PR_SET_PDEATHSIG
        raise OSError(ctypes.get_errno(), "prctl(PR_SET_PDEATHSIG) failed")


power_guard = ResearchPowerGuard()
