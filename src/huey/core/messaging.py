# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Messaging module (huey/core)

"""Messaging protocol primitives for inter-component communication.

This module defines the internal envelope structure used by HueyOS
subsystems (HostOS, SubOS, NanoOS, and external modules). The protocol is
designed around ZeroMQ message frames but the JSON encoding is transport
agnostic and may also be carried over MQTT topics.

Each message is composed of a :class:`MessageEnvelope` with a structured
header containing routing metadata, priority details, and health hints. The
payload remains an arbitrary JSON object to keep the protocol flexible while
still allowing schema validation via :class:`pydantic.BaseModel`.
"""

from __future__ import annotations

import json
import time
import uuid
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class Component(str, Enum):
    """Enumerates all known logical communication endpoints."""

    HOST_OS = "host_os"
    SUB_OS = "sub_os"
    NANO_OS = "nano_os"
    SPARK = "spark"
    ZAP = "zap"
    EXTERNAL_MODULE = "external_module"


class Transport(str, Enum):
    """Supported transport layers for the messaging protocol."""

    ZEROMQ = "zeromq"
    MQTT = "mqtt"


class MessagePriority(int, Enum):
    """Priority levels compatible with ZeroMQ and MQTT QoS semantics."""

    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class MessageHeader(BaseModel):
    """Structured metadata that precedes all message payloads."""

    schema_version: str = Field(
        "1.0",
        description="Semantic version of the envelope schema for compatibility.",
    )
    message_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        description="Unique identifier for this message instance.",
    )
    correlation_id: Optional[str] = Field(
        None,
        description="Identifier linking request / response message flows.",
    )
    reply_to: Optional[str] = Field(
        None,
        description="Logical component or topic for directed replies.",
    )
    sender: Component = Field(..., description="Originating component identifier.")
    recipient: Component = Field(
        ..., description="Intended recipient component or broadcast scope."
    )
    topic: str = Field(
        ..., description="Topic or channel name within the transport fabric."
    )
    priority: MessagePriority = Field(
        MessagePriority.NORMAL,
        description="Priority weighting used for queue ordering and QoS.",
    )
    transport: Transport = Field(
        Transport.ZEROMQ,
        description="Transport mechanism expected to deliver the message.",
    )
    timestamp: float = Field(
        default_factory=lambda: time.time(),
        description="Unix epoch timestamp at message creation.",
    )
    expiry: Optional[float] = Field(
        None,
        description=(
            "Optional unix epoch after which the recipient should discard the "
            "message if not yet processed."
        ),
    )
    requires_ack: bool = Field(
        False,
        description="True when the sender expects an acknowledgement message.",
    )

    @field_validator("topic")
    @classmethod
    def _validate_topic(cls, value: str) -> str:
        if not value:
            raise ValueError("message topic must be a non-empty string")
        return value


class MessageEnvelope(BaseModel):
    """Full message wrapper used across transports."""

    header: MessageHeader
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary JSON compatible payload to deliver to recipient.",
    )
    signature: Optional[str] = Field(
        None,
        description="Optional detached signature for tamper detection.",
    )

    def to_json(self) -> str:
        """Serialise the envelope to a canonical JSON string."""

        return self.json(sort_keys=True)

    def to_bytes(self) -> bytes:
        """Serialise the envelope to UTF-8 encoded bytes."""

        return self.to_json().encode("utf-8")

    @classmethod
    def from_json(cls, data: str) -> "MessageEnvelope":
        """Deserialize a :class:`MessageEnvelope` from JSON text."""

        return cls.parse_raw(data)

    @classmethod
    def from_bytes(cls, data: bytes) -> "MessageEnvelope":
        """Deserialize a :class:`MessageEnvelope` from bytes."""

        return cls.from_json(data.decode("utf-8"))

    def build_ack(
        self, status: str, payload: Optional[Dict[str, Any]] = None
    ) -> "MessageEnvelope":
        """Create a reply envelope acknowledging the current message."""

        if not self.header.reply_to:
            raise ValueError("cannot build acknowledgement without reply_to")
        reply_header = MessageHeader(
            sender=self.header.recipient,
            recipient=self.header.sender,
            topic=self.header.reply_to,
            correlation_id=self.header.message_id,
            priority=self.header.priority,
            transport=self.header.transport,
        )
        ack_payload = {"status": status}
        if payload:
            ack_payload.update(payload)
        return MessageEnvelope(header=reply_header, payload=ack_payload)


def encode_envelope(envelope: MessageEnvelope) -> bytes:
    """Helper for use with ZeroMQ multipart frames."""

    return envelope.to_bytes()


def decode_envelope(raw: bytes) -> MessageEnvelope:
    """Decode bytes received from a transport back into an envelope."""

    return MessageEnvelope.from_bytes(raw)


def envelope_from_components(
    *,
    sender: Component,
    recipient: Component,
    topic: str,
    payload: Optional[Dict[str, Any]] = None,
    priority: MessagePriority = MessagePriority.NORMAL,
    correlation_id: Optional[str] = None,
    reply_to: Optional[str] = None,
    transport: Transport = Transport.ZEROMQ,
    expiry: Optional[float] = None,
    requires_ack: bool = False,
) -> MessageEnvelope:
    """Create a :class:`MessageEnvelope` from primitive components."""

    header = MessageHeader(
        sender=sender,
        recipient=recipient,
        topic=topic,
        priority=priority,
        correlation_id=correlation_id,
        reply_to=reply_to,
        transport=transport,
        expiry=expiry,
        requires_ack=requires_ack,
    )
    return MessageEnvelope(header=header, payload=payload or {})


def pretty_print_envelope(envelope: MessageEnvelope) -> str:
    """Return a human readable version of the envelope for logging."""

    return json.dumps(json.loads(envelope.to_json()), indent=2, sort_keys=True)
