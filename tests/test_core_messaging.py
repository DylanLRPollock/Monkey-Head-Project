"""Regression coverage for the core messaging envelope helpers."""

from __future__ import annotations

import json

from huey.core.messaging import (
    Component,
    MessageEnvelope,
    MessagePriority,
    Transport,
    decode_envelope,
    encode_envelope,
    envelope_from_components,
)


def test_message_envelope_round_trip_uses_current_pydantic_api() -> None:
    envelope = envelope_from_components(
        sender=Component.HOST_OS,
        recipient=Component.SPARK,
        topic="huey.runtime.status",
        payload={"state": "ok", "count": 3},
        priority=MessagePriority.HIGH,
        correlation_id="corr-1",
        reply_to="huey.runtime.reply",
        transport=Transport.MQTT,
        requires_ack=True,
    )

    restored = MessageEnvelope.from_json(envelope.to_json())
    assert restored.model_dump() == envelope.model_dump()

    encoded = encode_envelope(envelope)
    decoded = decode_envelope(encoded)
    assert decoded.model_dump() == envelope.model_dump()


def test_message_envelope_pretty_json_remains_object_shaped() -> None:
    envelope = envelope_from_components(
        sender=Component.HOST_OS,
        recipient=Component.NANO_OS,
        topic="huey.health",
        payload={"status": "ok"},
    )

    payload = json.loads(envelope.to_json())
    assert payload["header"]["topic"] == "huey.health"
    assert payload["payload"] == {"status": "ok"}
