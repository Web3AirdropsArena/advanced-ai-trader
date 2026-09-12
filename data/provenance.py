from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class Provenance:
    source: str
    source_version: str
    observed_at: datetime
    received_at: datetime
    payload_hash: str

    @classmethod
    def from_payload(
        cls,
        *,
        source: str,
        source_version: str,
        observed_at: datetime,
        received_at: datetime,
        payload: Any,
    ) -> Provenance:
        if not source.strip() or not source_version.strip():
            raise ValueError("source and source_version must not be empty")
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        if received_at.tzinfo is None or received_at.utcoffset() is None:
            raise ValueError("received_at must be timezone-aware")

        observed_utc = observed_at.astimezone(UTC)
        received_utc = received_at.astimezone(UTC)
        if received_utc < observed_utc:
            raise ValueError("received_at cannot precede observed_at")

        try:
            canonical = json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
                default=_canonical_default,
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("payload is not canonically serializable") from exc

        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return cls(source, source_version, observed_utc, received_utc, digest)

    def as_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "source_version": self.source_version,
            "observed_at": self.observed_at.isoformat(),
            "received_at": self.received_at.isoformat(),
            "payload_hash": self.payload_hash,
        }


def _canonical_default(value: Any) -> str:
    """Provide deterministic serialization only for explicitly supported types."""
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise TypeError("datetime payload values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    raise TypeError(f"unsupported payload type: {type(value).__name__}")
