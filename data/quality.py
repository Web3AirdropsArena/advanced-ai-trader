from __future__ import annotations

from datetime import datetime, timezone

from data.contracts import DataQuality, Observation, DataQualityReport


class DataQualityGate:
    """Conservative first-pass quality gate.

    More advanced cross-source reconciliation belongs in the data service. This
    gate establishes a deterministic contract that downstream models can trust.
    """

    def evaluate(self, observation: Observation) -> DataQualityReport:
        reasons: list[str] = []

        if observation.received_at < observation.observed_at:
            reasons.append("received timestamp precedes observation timestamp")

        if observation.source_reliability < 0.50:
            reasons.append("source reliability below minimum threshold")

        if observation.quality == DataQuality.QUARANTINED:
            reasons.append("observation was already quarantined")

        accepted = not reasons
        quality = observation.quality if accepted else DataQuality.QUARANTINED

        return DataQualityReport(
            accepted=accepted,
            quality=quality,
            reliability=observation.source_reliability,
            reasons=reasons,
            checked_at=datetime.now(timezone.utc),
            source=observation.source,
        )
