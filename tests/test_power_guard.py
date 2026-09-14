from __future__ import annotations

from research.power_guard import ResearchPowerGuard


def test_power_guard_reports_unavailable_without_systemd(monkeypatch) -> None:
    monkeypatch.setattr("research.power_guard.shutil.which", lambda _: None)
    guard = ResearchPowerGuard()
    assert guard.available is False
    assert guard.acquire() is False
    assert guard.status() == {"available": False, "active": False}
    guard.release()


def test_power_guard_releases_inhibitor(monkeypatch) -> None:
    class FakeProcess:
        def __init__(self) -> None:
            self.returncode = None
            self.terminated = False

        def poll(self):
            return self.returncode

        def terminate(self) -> None:
            self.terminated = True
            self.returncode = 0

        def wait(self, timeout: float) -> int:
            return 0

    process = FakeProcess()
    monkeypatch.setattr("research.power_guard.os.name", "posix")
    monkeypatch.setattr("research.power_guard.shutil.which", lambda _: "/usr/bin/systemd-inhibit")
    monkeypatch.setattr("research.power_guard.subprocess.Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr("research.power_guard.sys_platform_linux", lambda: False)

    guard = ResearchPowerGuard()
    assert guard.acquire() is True
    assert guard.status()["active"] is True
    guard.release()
    assert process.terminated is True
    assert guard.status()["active"] is False
