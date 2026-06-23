"""Huey Internal Messaging System (HIMS) foundation.

The first HIMS implementation is deliberately small and local-first.  It uses
append-only JSON Lines files so messages and message state transitions remain
inspectable, durable, and easy to replay during HueyOS development.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

JSONValue = str | int | float | bool | None | dict[str, Any] | list[Any]


class MessagePriority(StrEnum):
    """Supported HIMS message priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageStatus(StrEnum):
    """Append-only lifecycle events understood by HIMS."""

    QUEUED = "queued"
    DELIVERED = "delivered"
    READ = "read"
    ARCHIVED = "archived"


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp with a stable ``Z`` suffix."""

    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _message_id() -> str:
    """Return a stable HIMS message identifier."""

    return f"hims-{uuid4().hex}"


def _event_id() -> str:
    """Return a stable HIMS event identifier."""

    return f"hims-event-{uuid4().hex}"


def default_hims_root() -> Path:
    """Return the default local HIMS storage root.

    The root can be overridden with ``HUEY_HIMS_ROOT``.  When unset, HIMS writes
    below ``.huey/hims`` relative to the current working directory so local runs
    do not pollute source packages or memory implementation modules.
    """

    configured = os.environ.get("HUEY_HIMS_ROOT")
    return Path(configured).expanduser() if configured else Path(".huey") / "hims"


@dataclass(frozen=True)
class HIMSMessage:
    """Immutable internal message envelope."""

    sender: str
    recipient: str
    body: str
    channel: str = "general"
    subject: str = ""
    message_id: str = field(default_factory=_message_id)
    created_at: str = field(default_factory=_utc_now)
    priority: MessagePriority | str = MessagePriority.NORMAL
    correlation_id: str | None = None
    parent_message_id: str | None = None
    tags: tuple[str, ...] = ()
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize the message to a JSON-safe dictionary."""

        payload = asdict(self)
        payload["priority"] = str(self.priority)
        payload["tags"] = list(self.tags)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> HIMSMessage:
        """Deserialize a message from a JSON-safe dictionary."""

        data = dict(payload)
        data["tags"] = tuple(data.get("tags") or ())
        data["priority"] = MessagePriority(data.get("priority", MessagePriority.NORMAL))
        return cls(**data)


@dataclass(frozen=True)
class HIMSEvent:
    """Append-only message lifecycle event."""

    message_id: str
    event_type: MessageStatus | str
    actor: str
    event_id: str = field(default_factory=_event_id)
    created_at: str = field(default_factory=_utc_now)
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize the event to a JSON-safe dictionary."""

        payload = asdict(self)
        payload["event_type"] = str(self.event_type)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> HIMSEvent:
        """Deserialize an event from a JSON-safe dictionary."""

        data = dict(payload)
        data["event_type"] = MessageStatus(data["event_type"])
        return cls(**data)


class HIMSStore:
    """Append-only JSONL message store for local Huey subsystems."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root).expanduser() if root is not None else default_hims_root()
        self.root.mkdir(parents=True, exist_ok=True)
        self.messages_path = self.root / "messages.jsonl"
        self.events_path = self.root / "events.jsonl"

    def send(
        self,
        *,
        sender: str,
        recipient: str,
        body: str,
        channel: str = "general",
        subject: str = "",
        priority: MessagePriority | str = MessagePriority.NORMAL,
        correlation_id: str | None = None,
        parent_message_id: str | None = None,
        tags: Iterable[str] = (),
        metadata: dict[str, JSONValue] | None = None,
    ) -> HIMSMessage:
        """Create and append a message, then record a queued event."""

        message = HIMSMessage(
            sender=sender,
            recipient=recipient,
            body=body,
            channel=channel,
            subject=subject,
            priority=MessagePriority(priority),
            correlation_id=correlation_id,
            parent_message_id=parent_message_id,
            tags=tuple(tags),
            metadata=metadata or {},
        )
        self.append_message(message)
        self.record_event(
            message.message_id,
            MessageStatus.QUEUED,
            actor=sender,
            metadata={"recipient": recipient, "channel": channel},
        )
        return message

    def append_message(self, message: HIMSMessage) -> None:
        """Append ``message`` to the message journal."""

        self._append_jsonl(self.messages_path, message.to_dict())

    def record_event(
        self,
        message_id: str,
        event_type: MessageStatus | str,
        *,
        actor: str,
        metadata: dict[str, JSONValue] | None = None,
    ) -> HIMSEvent:
        """Append a lifecycle event to the event journal."""

        if self.get_message(message_id) is None:
            raise KeyError(f"Unknown HIMS message: {message_id}")
        event = HIMSEvent(
            message_id=message_id,
            event_type=MessageStatus(event_type),
            actor=actor,
            metadata=metadata or {},
        )
        self._append_jsonl(self.events_path, event.to_dict())
        return event

    def mark_delivered(self, message_id: str, *, actor: str) -> HIMSEvent:
        """Record that a message has been delivered."""

        return self.record_event(message_id, MessageStatus.DELIVERED, actor=actor)

    def mark_read(self, message_id: str, *, actor: str) -> HIMSEvent:
        """Record that a message has been read."""

        return self.record_event(message_id, MessageStatus.READ, actor=actor)

    def archive(self, message_id: str, *, actor: str) -> HIMSEvent:
        """Record that a message has been archived."""

        return self.record_event(message_id, MessageStatus.ARCHIVED, actor=actor)

    def list_messages(self) -> list[HIMSMessage]:
        """Return every message in append order."""

        return [HIMSMessage.from_dict(row) for row in self._read_jsonl(self.messages_path)]

    def get_message(self, message_id: str) -> HIMSMessage | None:
        """Return one message by id, or ``None`` when absent."""

        for message in self.list_messages():
            if message.message_id == message_id:
                return message
        return None

    def inbox(self, recipient: str, *, include_archived: bool = False) -> list[HIMSMessage]:
        """Return messages addressed to ``recipient``."""

        messages = [m for m in self.list_messages() if m.recipient == recipient]
        if include_archived:
            return messages
        return [m for m in messages if self.status_for(m.message_id) != MessageStatus.ARCHIVED]

    def outbox(self, sender: str) -> list[HIMSMessage]:
        """Return messages sent by ``sender``."""

        return [m for m in self.list_messages() if m.sender == sender]

    def channel(self, channel: str) -> list[HIMSMessage]:
        """Return messages sent on ``channel``."""

        return [m for m in self.list_messages() if m.channel == channel]

    def events_for(self, message_id: str) -> list[HIMSEvent]:
        """Return lifecycle events for a message in append order."""

        return [
            HIMSEvent.from_dict(row)
            for row in self._read_jsonl(self.events_path)
            if row.get("message_id") == message_id
        ]

    def status_for(self, message_id: str) -> MessageStatus:
        """Return the latest known status for a message."""

        events = self.events_for(message_id)
        if not events:
            if self.get_message(message_id) is None:
                raise KeyError(f"Unknown HIMS message: {message_id}")
            return MessageStatus.QUEUED
        return MessageStatus(events[-1].event_type)

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, JSONValue]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
            handle.write("\n")

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    rows.append(json.loads(stripped))
        return rows


__all__ = [
    "HIMSEvent",
    "HIMSMessage",
    "HIMSStore",
    "JSONValue",
    "MessagePriority",
    "MessageStatus",
    "default_hims_root",
]
