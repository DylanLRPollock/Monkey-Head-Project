"""Regression coverage for the core messaging envelope helpers."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

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


def test_acknowledgement_preserves_routing_and_correlation() -> None:
    request = envelope_from_components(
        sender=Component.HOST_OS,
        recipient=Component.NANO_OS,
        topic="huey.command",
        reply_to="huey.command.ack",
        payload={"command": "healthcheck"},
        priority=MessagePriority.CRITICAL,
        transport=Transport.MQTT,
    )

    ack = request.build_ack("ok", {"latency_ms": 3})
    assert ack.header.sender == request.header.recipient
    assert ack.header.recipient == request.header.sender
    assert ack.header.topic == "huey.command.ack"
    assert ack.header.correlation_id == request.header.message_id
    assert ack.header.message_id != request.header.message_id
    assert ack.header.priority == MessagePriority.CRITICAL
    assert ack.header.transport == Transport.MQTT
    assert ack.payload == {"status": "ok", "latency_ms": 3}


def test_acknowledgement_requires_reply_destination() -> None:
    request = envelope_from_components(
        sender=Component.HOST_OS,
        recipient=Component.SPARK,
        topic="huey.command",
    )
    with pytest.raises(ValueError, match="reply_to"):
        request.build_ack("ok")


def test_envelope_rejects_empty_topic() -> None:
    with pytest.raises(ValidationError, match="message topic"):
        envelope_from_components(
            sender=Component.HOST_OS,
            recipient=Component.SPARK,
            topic="",
        )


def test_messages_do_not_share_mutable_payloads_or_identifiers() -> None:
    first = envelope_from_components(
        sender=Component.HOST_OS,
        recipient=Component.SPARK,
        topic="huey.test",
    )
    second = envelope_from_components(
        sender=Component.HOST_OS,
        recipient=Component.SPARK,
        topic="huey.test",
    )
    first.payload["only"] = "first"
    assert second.payload == {}
    assert first.header.message_id != second.header.message_id


def test_unicode_payload_round_trips_through_wire_bytes() -> None:
    envelope = envelope_from_components(
        sender=Component.SPARK,
        recipient=Component.HOST_OS,
        topic="huey.localization",
        payload={"value": "été / 日本語"},
        expiry=1234567890.0,
    )
    restored = decode_envelope(encode_envelope(envelope))
    assert restored.payload == envelope.payload
    assert restored.header.expiry == 1234567890.0
