"""Schema primitives for shadow-mode HIMS records."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return datetime.now(tz=UTC).isoformat()


def json_safe(value: Any) -> Any:
    """Recursively coerce values into JSON-safe primitives."""

    if isinstance(value, Path):
        return str(value)
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


class TrustClass(StrEnum):
    """Trust classes defined by the HIMS doctrine."""

    EPHEMERAL = "0_ephemeral"
    ROUTINE_INTERNAL = "1_routine_internal"
    PEBBLE_PERSONAL = "2_pebble_personal"
    BRANCH_OR_OFFICE_RESTRICTED = "3_branch_or_office_restricted"
    CONSTITUTIONAL_OR_OFFICIAL_RECORD = "4_constitutional_or_official_record"
    SAFETY_OR_PRESERVATION_CRITICAL = "5_safety_or_preservation_critical"


class MessageStatus(StrEnum):
    """Shadow-mode message states aligned to the master plan."""

    DRAFT = "draft"
    SIGNED = "signed"
    ACCEPTED = "accepted"
    QUEUED = "queued"
    DELIVERED = "delivered"
    OPENED = "opened"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTING = "executing"
    EXECUTED = "executed"
    LOGGED = "logged"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class HIMSMessage:
    """One structured HIMS message snapshot."""

    sender: str
    recipient: str
    role_context: str
    intent_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    authority_requirement: str = ""
    status: MessageStatus = MessageStatus.DRAFT
    trust_class: TrustClass = TrustClass.ROUTINE_INTERNAL
    route: list[str] = field(default_factory=list)
    signature_or_validation_metadata: dict[str, Any] = field(default_factory=dict)
    lineage_metadata: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    reply_to: str | None = None
    timestamp: str = field(default_factory=utc_now)
    message_id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(json_safe(self.payload)))
        object.__setattr__(
            self,
            "signature_or_validation_metadata",
            dict(json_safe(self.signature_or_validation_metadata)),
        )
        object.__setattr__(
            self,
            "lineage_metadata",
            dict(json_safe(self.lineage_metadata)),
        )
        object.__setattr__(self, "route", [str(item) for item in self.route])

    def to_dict(self, *, current_mailbox: str | None = None) -> dict[str, Any]:
        """Return a JSON-safe record representation."""

        record = {
            "message_id": self.message_id,
            "from": self.sender,
            "to": self.recipient,
            "role_context": self.role_context,
            "intent_type": self.intent_type,
            "payload": json_safe(self.payload),
            "timestamp": self.timestamp,
            "authority_requirement": self.authority_requirement,
            "signature_or_validation_metadata": json_safe(
                self.signature_or_validation_metadata
            ),
            "lineage_metadata": json_safe(self.lineage_metadata),
            "status": self.status.value,
            "trust_class": self.trust_class.value,
            "route": list(self.route),
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
        }
        if current_mailbox is not None:
            record["current_mailbox"] = current_mailbox
        return record

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HIMSMessage":
        """Build a message from a stored record snapshot."""

        return cls(
            message_id=str(payload["message_id"]),
            sender=str(payload["from"]),
            recipient=str(payload["to"]),
            role_context=str(payload["role_context"]),
            intent_type=str(payload["intent_type"]),
            payload=dict(payload.get("payload", {})),
            timestamp=str(payload["timestamp"]),
            authority_requirement=str(payload.get("authority_requirement", "")),
            signature_or_validation_metadata=dict(
                payload.get("signature_or_validation_metadata", {})
            ),
            lineage_metadata=dict(payload.get("lineage_metadata", {})),
            status=MessageStatus(str(payload["status"])),
            trust_class=TrustClass(
                str(payload.get("trust_class", TrustClass.ROUTINE_INTERNAL.value))
            ),
            route=[str(item) for item in payload.get("route", [])],
            correlation_id=(
                str(payload["correlation_id"])
                if payload.get("correlation_id") is not None
                else None
            ),
            reply_to=(
                str(payload["reply_to"]) if payload.get("reply_to") is not None else None
            ),
        )

    def with_status(
        self,
        status: MessageStatus,
        *,
        payload_updates: dict[str, Any] | None = None,
        signature_updates: dict[str, Any] | None = None,
        lineage_updates: dict[str, Any] | None = None,
    ) -> "HIMSMessage":
        """Return a new message snapshot with an updated status."""

        payload = dict(self.payload)
        if payload_updates:
            payload.update(dict(json_safe(payload_updates)))

        signature_metadata = dict(self.signature_or_validation_metadata)
        if signature_updates:
            signature_metadata.update(dict(json_safe(signature_updates)))

        lineage_metadata = dict(self.lineage_metadata)
        if lineage_updates:
            lineage_metadata.update(dict(json_safe(lineage_updates)))

        return replace(
            self,
            payload=payload,
            signature_or_validation_metadata=signature_metadata,
            lineage_metadata=lineage_metadata,
            status=MessageStatus(status),
            timestamp=utc_now(),
        )


__all__ = ["HIMSMessage", "MessageStatus", "TrustClass", "json_safe", "utc_now"]
