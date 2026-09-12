from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from research.latent import LatentSnapshotStore


class LatentResearchSupervisor:
    """Background benchmark training with evolving penultimate-layer telemetry."""

    def __init__(self, state_path: str | Path = "data/runtime/research_status.json") -> None:
        self.state_path = Path(state_path)
        self.latent_store = LatentSnapshotStore()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._state: dict[str, Any] = {
            "status": "stopped", "stage": "idle", "experiment_id": None,
            "model_id": None, "progress": 0.0, "epoch": 0, "epochs": 0,
            "evaluation_interval": 2, "samples_processed": 0, "validation_loss": None,
            "heartbeat_at": None, "started_at": None, "finished_at": None,
            "dataset": "deterministic_benchmark_v1", "market_training": False,
            "latent_dimensions": 3, "latent_points": 0,
            "latent_snapshot": "data/runtime/latent_points.jsonl",
            "message": "Research supervisor has not started.",
        }

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="latent-research-supervisor", daemon=True)
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
                status="training", stage="training", experiment_id=experiment_id,
                model_id="mlp-benchmark", progress=0.0, epoch=0, epochs=epochs,
                evaluation_interval=2, samples_processed=0, validation_loss=None,
                started_at=started, finished_at=None, dataset="deterministic_benchmark_v1",
                market_training=False, latent_points=0,
                message="Training benchmark model and sampling its evolving penultimate representation.",
            )
            loss = self._train_benchmark(experiment_id, epochs)
            if self._stop.is_set():
                break
            self._set(status="completed", stage="evaluation", progress=100.0,
                      validation_loss=loss, finished_at=datetime.now(UTC).isoformat(),
                      message="Benchmark training completed; waiting before next experiment.")
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
        hidden_size = 12
        hidden_weights = rng.normal(0, 0.35, size=(8, hidden_size))
        hidden_bias = np.zeros(hidden_size)
        output_weights = rng.normal(0, 0.1, size=hidden_size)
        output_bias = 0.0
        learning_rate = 0.03
        validation_loss = float("inf")

        for epoch in range(1, epochs + 1):
            if self._stop.is_set():
                return float("nan")
            hidden = np.tanh(train_x @ hidden_weights + hidden_bias)
            predictions = hidden @ output_weights + output_bias
            error = predictions - train_y
            grad_output = (2.0 / len(train_x)) * (hidden.T @ error)
            grad_output_bias = float(2.0 * error.mean())
            hidden_gradient = (error[:, None] * output_weights[None, :]) * (1.0 - hidden**2)
            grad_hidden_weights = (2.0 / len(train_x)) * (train_x.T @ hidden_gradient)
            grad_hidden_bias = 2.0 * hidden_gradient.mean(axis=0)
            output_weights -= learning_rate * grad_output
            output_bias -= learning_rate * grad_output_bias
            hidden_weights -= learning_rate * grad_hidden_weights
            hidden_bias -= learning_rate * grad_hidden_bias

            eval_hidden = np.tanh(test_x @ hidden_weights + hidden_bias)
            eval_predictions = eval_hidden @ output_weights + output_bias
            validation_loss = float(np.mean((eval_predictions - test_y) ** 2))
            self._set(progress=round(epoch * 100 / epochs, 2), epoch=epoch,
                      samples_processed=epoch * len(train_x), validation_loss=validation_loss,
                      stage="training")

            if epoch % 2 == 0 or epoch == 1:
                labels = np.where(test_y > 0.1, "BUY", np.where(test_y < -0.1, "SELL", "HOLD"))
                predicted = np.where(eval_predictions > 0.1, "BUY", np.where(eval_predictions < -0.1, "SELL", "HOLD"))
                count = self.latent_store.write_snapshot(
                    eval_hidden, epoch, predicted, labels, eval_predictions, max_samples=1500
                )
                self._set(stage="latent_evaluation", latent_points=count)
            time.sleep(0.15)
        return validation_loss

    @staticmethod
    def _experiment_id() -> str:
        stamp = datetime.now(UTC).isoformat()
        digest = hashlib.sha256(stamp.encode()).hexdigest()[:12]
        return f"exp-{digest}"


supervisor = LatentResearchSupervisor()
