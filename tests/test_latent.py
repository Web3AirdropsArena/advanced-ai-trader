from pathlib import Path

import numpy as np

from research.latent import LatentSnapshotStore, PCAReducer3D
from research.latent_api import load_latent_points


def test_pca_reduces_to_three_dimensions() -> None:
    rng = np.random.default_rng(7)
    projected = PCAReducer3D().fit_transform(rng.normal(size=(20, 8)))
    assert projected.shape == (20, 3)
    assert np.isfinite(projected).all()


def test_latent_store_caps_samples_and_keeps_metadata(tmp_path: Path) -> None:
    rng = np.random.default_rng(8)
    path = tmp_path / "latent.jsonl"
    store = LatentSnapshotStore(path, max_snapshots=2)
    representations = rng.normal(size=(10, 6))
    labels = ["BUY"] * 10
    count = store.write_snapshot(representations, 2, labels, labels, [0.1] * 10, max_samples=5)
    assert count == 5
    points = load_latent_points(path)
    assert len(points) == 5
    assert {point["epoch"] for point in points} == {2}
    assert all(set(point) == {"epoch", "pnl_or_return", "predicted_class", "timestamp", "true_label", "x", "y", "z"} for point in points)
