from datetime import UTC, datetime, timedelta

from data.provenance import Provenance
from data.quality_engine import QualityEngine


def test_stale_observation_is_rejected() -> None:
    observed = datetime(2026, 1, 1, tzinfo=UTC)
    received = observed + timedelta(seconds=61)
    result = QualityEngine().evaluate(
        observed_at=observed,
        received_at=received,
        source_reliability=0.99,
        values=[1.0, 2.0],
        max_age_seconds=60,
    )
    assert not result.accepted
    assert "stale" in result.reasons[0]


def test_clock_inversion_is_rejected() -> None:
    observed = datetime(2026, 1, 1, 0, 1, tzinfo=UTC)
    received = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    result = QualityEngine().evaluate(
        observed_at=observed,
        received_at=received,
        source_reliability=1.0,
        values=[1.0],
        max_age_seconds=60,
    )
    assert not result.accepted
    assert "receive time" in result.reasons[0]


def test_provenance_hash_is_deterministic() -> None:
    observed = datetime(2026, 1, 1, tzinfo=UTC)
    a = Provenance.from_payload(
        source="test",
        source_version="1",
        observed_at=observed,
        received_at=observed,
        payload={"b": 2, "a": 1},
    )
    b = Provenance.from_payload(
        source="test",
        source_version="1",
        observed_at=observed,
        received_at=observed,
        payload={"a": 1, "b": 2},
    )
    assert a.payload_hash == b.payload_hash
