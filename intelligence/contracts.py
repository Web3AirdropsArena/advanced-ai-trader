from __future__ import annotations

from pydantic import BaseModel, Field


class Prediction(BaseModel):
    asset_id: str
    horizon_seconds: int = Field(gt=0)
    expected_return: float
    uncertainty: float = Field(ge=0, le=1)
    regime_probability: dict[str, float] = Field(default_factory=dict)
    model_version: str


class ModelCandidate(BaseModel):
    name: str
    version: str
    hypothesis: str
    features: list[str]
    validation_score: float
    robustness_score: float
    uncertainty_score: float
    reproducibility_hash: str
    promoted: bool = False
