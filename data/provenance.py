from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
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
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return cls(source, source_version, observed_at, received_at, digest)

    def as_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "source_version": self.source_version,
            "observed_at": self.observed_at.isoformat(),
            "received_at": self.received_at.isoformat(),
            "payload_hash": self.payload_hash,
        }
