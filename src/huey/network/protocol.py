"""Protocol helpers for Huey message envelopes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass(slots=True)
class ProtocolEnvelope:
    topic: str
    payload: dict[str, object]
    headers: dict[str, str] = field(default_factory=dict)

    def encode(self) -> str:
        return json.dumps(
            {
                "topic": self.topic,
                "payload": self.payload,
                "headers": self.headers,
            },
            sort_keys=True,
        )

    @classmethod
    def decode(cls, payload: str) -> "ProtocolEnvelope":
        data = json.loads(payload)
        return cls(
            topic=str(data["topic"]),
            payload=dict(data.get("payload", {})),
            headers={str(key): str(value) for key, value in dict(data.get("headers", {})).items()},
        )


__all__ = ["ProtocolEnvelope"]
