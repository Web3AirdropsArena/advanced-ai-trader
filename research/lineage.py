from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from typing import Any


class ExperimentRecord(BaseModel):
    """Scientific record required before an artifact can become production knowledge."""

    experiment_id: str
    parent_experiment_id: str | None = None
    dataset_snapshot: str
    feature_snapshot: str
    code_revision: str
    dependency_lock_hash: str
    random_seed: int
    environment_fingerprint: str
    started_at: datetime
    finished_at: datetime | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)
    hypotheses_rejected: list[str] = Field(default_factory=list)
    reproducibility_hash: str

    @classmethod
    def now(cls, **kwargs: Any) -> ExperimentRecord:
    return cls(started_at=datetime.now(UTC), **kwargs)
