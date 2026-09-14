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
from research.terminal_ui import terminal_ui


class LatentResearchSupervisor:
    """Background benchmark training with bounded terminal/API telemetry."""

    def __init__(self, state_path: str | Path = "data/runtime/research_status.json") -> None:
        self.state_path = Path(state_path)
        self.history_path = self.state_path.with_name("research_history.json")
        self.events_path = self.state_path.with_name("research_events.jsonl")
        self.latent_store = LatentSnapshotStore()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._history: list[dict[str, Any]] = []
        self._events: list[dict[str, Any]] = []
        self._load_persistent_state()
        self._state: dict[str, Any] = {
            "status": "stopped", "stage": "stage_1_research", "experiment_id": None,
            "model_id": None, "progress": 0.0, "epoch": 0, "epochs": 0,
            "evaluation_interval": 2, "samples_processed": 0, "validation_loss": None,
            "heartbeat_at": None, "started_at": None, "finished_at": None,
            "dataset": "deterministic_benchmark_v1", "market_training": False,
            "latent_dimensions": 3, "latent_points": 0,
            "latent_snapshot": "data/runtime/latent_points.jsonl",
            "stage_one_complete": False, "next_stage_ready": False,
            "message": "Research stage has not started.",
        }

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run, name="latent-research-supervisor", daemon=True
            )
            self._thread.start()
        terminal_ui.banner()
        self._event("research_started", "Research supervisor started.")

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=2)
        with self._lock:
            self._state["status"] = "stopped"
            if not self._state["stage_one_complete"]:
                self._state["stage"] = "stage_1_research"
            self._state["message"] = "Research supervisor stopped."
            self._persist()
        self._event("research_stopped", "Research supervisor stopped by operator.")

    def mark_stage_one_complete(self, evidence: str) -> None:
        """Publish the Stage 1 -> Stage 2 handoff only after validation."""
        if not evidence.strip():
            raise ValueError("stage-one completion requires validation evidence")
        with self._lock:
            self._state["stage_one_complete"] = True
            self._state["next_stage_ready"] = True
            self._state["stage"] = "stage_1_complete"
            self._state["status"] = "completed"
            self._state["finished_at"] = datetime.now(UTC).isoformat()
            self._state["message"] = "STAGE 1 COMPLETE — validated research is ready for Stage 2."
            self._state["stage_one_evidence"] = evidence
            self._persist()
        self._event("stage_one_completed", "STAGE 1 COMPLETE — Stage 2 handoff is ready.", evidence=evidence)

    def status(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def history(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            return list(reversed(self._history[-max(1, min(limit, 100)) :]))

    def events(self, limit: int = 40) -> list[dict[str, Any]]:
        with self._lock:
            return list(reversed(self._events[-max(1, min(limit, 100)) :]))

    def _set(self, **updates: Any) -> None:
        with self._lock:
            self._state.update(updates)
            self._state["heartbeat_at"] = datetime.now(UTC).isoformat()
            state = dict(self._state)
            self._persist()
        terminal_ui.progress(state)

    def _persist(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.state_path)

    def _load_persistent_state(self) -> None:
        try:
            data = json.loads(self.history_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                self._history = [item for item in data if isinstance(item, dict)][-100:]
        except (OSError, ValueError):
            self._history = []
        try:
            lines = self.events_path.read_text(encoding="utf-8").splitlines()
            self._events = [json.loads(line) for line in lines[-100:] if line.strip()]
            self._events = [item for item in self._events if isinstance(item, dict)]
        except (OSError, ValueError):
            self._events = []

    def _event(self, event_type: str, message: str, **details: Any) -> None:
        event = {"timestamp": datetime.now(UTC).isoformat(), "type": event_type, "message": message, **details}
        with self._lock:
            self._events.append(event)
            self._events = self._events[-100:]
            self.events_path.parent.mkdir(parents=True, exist_ok=True)
            with self.events_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
        terminal_ui.event(event_type, message, **details)

    def _record_experiment(self, experiment_id: str, loss: float, started: str) -> None:
        record = {
            "experiment_id": experiment_id, "model_id": "mlp-benchmark",
            "dataset": "deterministic_benchmark_v1", "market_training": False,
            "status": "completed", "started_at": started,
            "finished_at": datetime.now(UTC).isoformat(), "epochs": 20,
            "validation_loss": None if not np.isfinite(loss) else loss,
            "latent_snapshot": "data/runtime/latent_points.jsonl",
        }
        with self._lock:
            self._history.append(record)
            self._history = self._history[-100:]
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.history_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(self._history, indent=2, sort_keys=True), encoding="utf-8")
            temporary.replace(self.history_path)
        self._event("experiment_completed", "Benchmark experiment completed.", experiment_id=experiment_id)

    def _run(self) -> None:
        while not self._stop.is_set() and not self._state["stage_one_complete"]:
            experiment_id = self._experiment_id()
            started = datetime.now(UTC).isoformat()
            epochs = 20
            self._set(
                status="training", stage="stage_1_research", experiment_id=experiment_id,
                model_id="mlp-benchmark", progress=0.0, epoch=0, epochs=epochs,
                evaluation_interval=2, samples_processed=0, validation_loss=None,
                started_at=started, finished_at=None, dataset="deterministic_benchmark_v1",
                market_training=False, latent_points=0,
                message="Training benchmark model and sampling its evolving penultimate representation.",
            )
            self._event("experiment_started", "Started benchmark experiment.", experiment_id=experiment_id)
            loss = self._train_benchmark(experiment_id, epochs)
            if self._stop.is_set():
                break
            self._set(
                status="completed", stage="stage_1_research_evaluation", progress=100.0,
                validation_loss=loss, finished_at=datetime.now(UTC).isoformat(),
                message="Experiment completed; Stage 1 continues until validation criteria are satisfied.",
            )
            self._record_experiment(experiment_id, loss, started)
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
                return validation_loss
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
            self._set(
                progress=round(epoch * 100 / epochs, 2), epoch=epoch,
                samples_processed=epoch * len(train_x), validation_loss=validation_loss,
                stage="stage_1_research_training",
            )
            self._event(
                "epoch_completed",
                f"Epoch {epoch}/{epochs} completed.",
                epoch=epoch,
                progress=round(epoch * 100 / epochs, 2),
                validation_loss=round(validation_loss, 6),
                samples=epoch * len(train_x),
            )
            if epoch % 2 == 0 or epoch == 1:
                labels = np.where(test_y > 0.1, "BUY", np.where(test_y < -0.1, "SELL", "HOLD"))
                predicted = np.where(eval_predictions > 0.1, "BUY", np.where(eval_predictions < -0.1, "SELL", "HOLD"))
                count = self.latent_store.write_snapshot(
                    eval_hidden, epoch, [str(value) for value in predicted.tolist()],
                    [str(value) for value in labels.tolist()],
                    [float(value) for value in eval_predictions.tolist()], max_samples=1500,
                )
                self._set(stage="stage_1_latent_evaluation", latent_points=count)
                self._event("latent_snapshot", f"Captured {count} latent points from epoch {epoch}.", epoch=epoch, points=count)
            time.sleep(0.15)
        return validation_loss

    @staticmethod
    def _experiment_id() -> str:
        stamp = datetime.now(UTC).isoformat()
        digest = hashlib.sha256(stamp.encode()).hexdigest()[:12]
        return f"exp-{digest}"


supervisor = LatentResearchSupervisor()
