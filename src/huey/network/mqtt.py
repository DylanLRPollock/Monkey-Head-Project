"""MQTT client profile abstraction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MQTTProfile:
    host: str
    port: int = 1883
    topic_prefix: str = "huey"


class MQTTClient:
    """Retain the last published payload per topic."""

    def __init__(self, profile: MQTTProfile) -> None:
        self.profile = profile
        self._topics: dict[str, str] = {}

    def publish(self, topic: str, payload: str) -> dict[str, object]:
        full_topic = f"{self.profile.topic_prefix}/{topic}".strip("/")
        self._topics[full_topic] = payload
        return {"topic": full_topic, "payload": payload}

    def snapshot(self) -> dict[str, str]:
        return dict(self._topics)


__all__ = ["MQTTClient", "MQTTProfile"]
