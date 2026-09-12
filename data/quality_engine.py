from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import isfinite


@dataclass(frozen=True)
class QualityResult:
    score: float
    accepted: bool
    reasons: tuple[str, ...]


class QualityEngine:
    """Reject obviously unsafe observations before they reach research or execution."""

    def __init__(self, *, minimum_score: float = 0.70) -> None:
        if not isfinite(minimum_score) or not 0 <= minimum_score <= 1:
            raise ValueError("minimum_score must be finite and between 0 and 1")
        self.minimum_score = minimum_score

    def evaluate(
        self,
        *,
        observed_at: datetime,
        received_at: datetime,
        source_reliability: float,
        values: list[float],
        max_age_seconds: float,
    ) -> QualityResult:
        reasons: list[str] = []

        if not isfinite(source_reliability) or not 0 <= source_reliability <= 1:
            return QualityResult(0.0, False, ("source reliability is invalid",))
        if not isfinite(max_age_seconds) or max_age_seconds < 0:
            return QualityResult(0.0, False, ("maximum observation age is invalid",))
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            return QualityResult(0.0, False, ("observation time must be timezone-aware",))
        if received_at.tzinfo is None or received_at.utcoffset() is None:
            return QualityResult(0.0, False, ("receive time must be timezone-aware",))

        # Normalize offsets before comparing so DST/offset differences cannot
        # silently turn a valid observation into a negative or stale age.
        observed_utc = observed_at.astimezone(UTC)
        received_utc = received_at.astimezone(UTC)
        score = source_reliability

        if not values:
            return QualityResult(0.0, False, ("observation contains no values",))

        if any(not isfinite(value) for value in values):
            return QualityResult(0.0, False, ("observation contains non-finite values",))

        if received_utc < observed_utc:
            return QualityResult(0.0, False, ("receive time precedes observation time",))

        age = (received_utc - observed_utc).total_seconds()
        if age > max_age_seconds:
            reasons.append("observation is stale")
            score *= 0.4

        if source_reliability < 0.5:
            reasons.append("source reliability is below baseline")
            score *= 0.6

        accepted = score >= self.minimum_score and not reasons
        if not accepted and not reasons:
            reasons.append("quality score below acceptance threshold")

        return QualityResult(score=score, accepted=accepted, reasons=tuple(reasons))
