from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class LatentPoint:
    """One projected representation with training/evaluation metadata."""

    x: float
    y: float
    z: float
    epoch: int
    timestamp: str
    predicted_class: str
    true_label: str
    pnl_or_return: float


class PCAReducer3D:
    """Small NumPy-only PCA implementation for low-overhead 3D projections."""

    def __init__(self, n_components: int = 3) -> None:
        if n_components != 3:
            raise ValueError("The latent visualization requires exactly 3 components.")
        self.n_components = n_components

    def fit_transform(self, representations: NDArray[np.float64]) -> NDArray[np.float64]:
        matrix: NDArray[np.float64] = np.asarray(representations, dtype=np.float64)
        if matrix.ndim != 2:
            raise ValueError("Representations must be a 2D matrix.")
        if matrix.shape[0] < 3:
            raise ValueError("At least 3 samples are required for a 3D projection.")
        if not np.isfinite(matrix).all():
            raise ValueError("Representations contain non-finite values.")

        centered: NDArray[np.float64] = matrix - matrix.mean(axis=0, keepdims=True)
        scale: NDArray[np.float64] = centered.std(axis=0, keepdims=True)
        scale[scale < 1e-12] = 1.0
        normalized: NDArray[np.float64] = centered / scale
        _, _, vh = np.linalg.svd(normalized, full_matrices=False)
        components: NDArray[np.float64] = vh[: self.n_components].T
        return np.asarray(normalized @ components, dtype=np.float64)


class LatentSnapshotStore:
    """Append bounded latent snapshots for the dashboard and standalone renderer."""

    def __init__(self, path: str | Path = "data/runtime/latent_points.jsonl", max_snapshots: int = 20) -> None:
        self.path = Path(path)
        self.max_snapshots = max(1, max_snapshots)

    def write_snapshot(
        self,
        representations: NDArray[np.float64],
        epoch: int,
        predicted_class: Sequence[str],
        true_label: Sequence[str],
        pnl_or_return: Sequence[float],
        max_samples: int = 1500,
    ) -> int:
        matrix: NDArray[np.float64] = np.asarray(representations, dtype=np.float64)
        count = matrix.shape[0]
        if matrix.ndim != 2 or count == 0:
            raise ValueError("A non-empty 2D representation matrix is required.")
        if not (len(predicted_class) == len(true_label) == len(pnl_or_return) == count):
            raise ValueError("Latent metadata lengths must match representation rows.")

        limit = max(3, max_samples)
        indices = np.arange(count)
        if count > limit:
            indices = indices[-limit:]
        sampled = matrix[indices]
        coordinates: NDArray[np.float64] = PCAReducer3D().fit_transform(sampled)
        timestamp = datetime.now(UTC).isoformat()
        points = [
            LatentPoint(
                x=float(coords[0]),
                y=float(coords[1]),
                z=float(coords[2]),
                epoch=epoch,
                timestamp=timestamp,
                predicted_class=str(predicted_class[int(index)]),
                true_label=str(true_label[int(index)]),
                pnl_or_return=float(pnl_or_return[int(index)]),
            )
            for coords, index in zip(coordinates, indices, strict=True)
        ]

        existing = self._read_snapshots()
        existing.append(points)
        existing = existing[-self.max_snapshots :]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            for snapshot in existing:
                for point in snapshot:
                    handle.write(json.dumps(asdict(point), sort_keys=True) + "\n")
        temporary.replace(self.path)
        return len(points)

    def _read_snapshots(self) -> list[list[LatentPoint]]:
        if not self.path.exists():
            return []
        groups: dict[int, list[LatentPoint]] = {}
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            point = LatentPoint(**payload)
            groups.setdefault(point.epoch, []).append(point)
        return [groups[key] for key in sorted(groups)]
