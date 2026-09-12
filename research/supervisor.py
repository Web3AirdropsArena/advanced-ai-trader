from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np


class ResearchSupervisor:
    """Background research worker with real training telemetry.

    The default workload is an explicitly labelled deterministic benchmark, not
    market data. This proves the training/heartbeat pipeline without pretending
    that a trading model is being trained before a market dataset is connected.
    """

    def __init__(self, state_path: str | Path = "data/runtime/research_status.json") -> None:
        self.state_path = Path(state_path)
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._state: dict[str, Any] = {
            "status": "stopped",
            "stage": "idle",
            "experiment_id": None,
            "model_id": None,
            "progress": 0.0,
            "epoch": 0,
            "epochs": 0,
            "samples_processed": 0,
            "validation_loss": None,
            "heartbeat_at": None,
            "started_at": None,
            "finished_at": None,
            "dataset": "deterministic_benchmark_v1",
            "market_training": False,
            "message": "Research supervisor has not started.",
        }

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="research-supervisor",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=2)
        with self._lock:
            self._state["status"] = "stopped"
            self._state["stage"] = "idle"
            self._state["message"] = "Research supervisor stopped."
            self._persist()

    def status(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def _set(self, **updates: Any) -> None:
        with self._lock:
            self._state.update(updates)
            self._state["heartbeat_at"] = datetime.now(UTC).isoformat()
            self._persist()

    def _persist(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.state_path)

    def _run(self) -> None:
        while not self._stop.is_set():
            experiment_id = self._experiment_id()
            started = datetime.now(UTC).isoformat()
            epochs = 20
            self._set(
                status="training",
                stage="benchmark_training",
                experiment_id=experiment_id,
                model_id="ridge-benchmark",
                progress=0.0,
                epoch=0,
                epochs=epochs,
                samples_processed=0,
                validation_loss=None,
                started_at=started,
                finished_at=None,
                dataset="deterministic_benchmark_v1",
                market_training=False,
                message=(
                    "Training benchmark model. Market-data training is not enabled "
                    "until a validated market dataset is connected."
                ),
            )

            loss = self._train_benchmark(experiment_id, epochs)
            if self._stop.is_set():
                break

            self._set(
                status="completed",
                stage="evaluation",
                progress=100.0,
                validation_loss=loss,
                finished_at=datetime.now(UTC).isoformat(),
                message="Benchmark training completed; waiting before next experiment.",
            )
            self._stop.wait(5)

    def _train_benchmark(self, experiment_id: str, epochs: int) -> float:
        seed = int(experiment_id[-8:], 16) % (2**32)
        rng = np.random.default_rng(seed)
        x = rng.normal(size=(4000, 8))
        weights = np.array([0.8, -0.4, 0.25, 0.1, 0.05, -0.2, 0.3, 0.15])
        y = x @ weights + rng.normal(0, 0.15, size=4000)
        split = 3200
        train_x, test_x = x[:split], x[split:]
        train_y, test_y = y[:split], y[split:]
        regularization = 0.01
        identity = np.eye(train_x.shape[1])
        fitted = np.linalg.solve(
            train_x.T @ train_x + regularization * identity,
            train_x.T @ train_y,
        )

        for epoch in range(1, epochs + 1):
            if self._stop.is_set():
                return float("nan")
            # Re-fit against an expanding prefix to make each epoch real work.
            end = max(64, int(split * epoch / epochs))
            prefix_x, prefix_y = train_x[:end], train_y[:end]
            fitted = np.linalg.solve(
                prefix_x.T @ prefix_x + regularization * identity,
                prefix_x.T @ prefix_y,
            )
            validation_loss = float(np.mean((test_x @ fitted - test_y) ** 2))
            self._set(
                progress=round(epoch * 100 / epochs, 2),
                epoch=epoch,
                samples_processed=end,
                validation_loss=validation_loss,
            )
            time.sleep(0.15)
        return float(np.mean((test_x @ fitted - test_y) ** 2))

    @staticmethod
    def _experiment_id() -> str:
        stamp = datetime.now(UTC).isoformat()
        digest = hashlib.sha256(stamp.encode()).hexdigest()[:12]
        return f"exp-{digest}"


supervisor = ResearchSupervisor()
