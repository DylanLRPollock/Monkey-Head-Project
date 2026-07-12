"""Validation helpers for shadow-mode HIMS messages and transitions."""

from __future__ import annotations

from huey.hims.schema import HIMSMessage, MessageStatus

_ALLOWED_STATUSES_BY_INTENT: dict[str, set[MessageStatus]] = {
    "external_interface_packet": {
        MessageStatus.ACCEPTED,
        MessageStatus.ARCHIVED,
    },
    "request": {
        MessageStatus.QUEUED,
        MessageStatus.ACCEPTED,
        MessageStatus.REJECTED,
        MessageStatus.EXECUTING,
        MessageStatus.EXECUTED,
        MessageStatus.ARCHIVED,
    },
    "report": {
        MessageStatus.EXECUTED,
        MessageStatus.ARCHIVED,
    },
    "alert": {
        MessageStatus.EXECUTED,
        MessageStatus.ARCHIVED,
    },
    "archived_record": {MessageStatus.ARCHIVED},
}

_ALLOWED_TRANSITIONS: dict[str, dict[MessageStatus, set[MessageStatus]]] = {
    "external_interface_packet": {
        MessageStatus.ACCEPTED: {MessageStatus.ARCHIVED},
    },
    "request": {
        MessageStatus.QUEUED: {
            MessageStatus.ACCEPTED,
            MessageStatus.REJECTED,
        },
        MessageStatus.ACCEPTED: {
            MessageStatus.EXECUTING,
            MessageStatus.EXECUTED,
            MessageStatus.ARCHIVED,
        },
        MessageStatus.EXECUTING: {
            MessageStatus.EXECUTED,
            MessageStatus.REJECTED,
        },
        MessageStatus.EXECUTED: {MessageStatus.ARCHIVED},
        MessageStatus.REJECTED: {MessageStatus.ARCHIVED},
    },
    "report": {
        MessageStatus.EXECUTED: {MessageStatus.ARCHIVED},
    },
    "alert": {
        MessageStatus.EXECUTED: {MessageStatus.ARCHIVED},
    },
}


def validate_hims_message(message: HIMSMessage) -> None:
    """Raise when a shadow-mode HIMS message is malformed."""

    if not message.sender.strip():
        raise ValueError("message sender is required")
    if not message.recipient.strip():
        raise ValueError("message recipient is required")
    if not message.role_context.strip():
        raise ValueError("message role_context is required")
    if not message.intent_type.strip():
        raise ValueError("message intent_type is required")
    if not message.authority_requirement.strip():
        raise ValueError("message authority_requirement is required")
    if not message.route:
        raise ValueError("message route must contain at least one step")

    allowed_statuses = _ALLOWED_STATUSES_BY_INTENT.get(message.intent_type)
    if allowed_statuses is None:
        raise ValueError(f"unsupported intent_type: {message.intent_type}")
    if message.status not in allowed_statuses:
        raise ValueError(
            f"status {message.status.value} is not valid for {message.intent_type}"
        )

    root_lineage_id = str(message.lineage_metadata.get("root_lineage_id", "")).strip()
    if not root_lineage_id:
        raise ValueError("lineage_metadata.root_lineage_id is required")

    if message.intent_type != "external_interface_packet":
        parent_message_id = str(
            message.lineage_metadata.get("parent_message_id", "")
        ).strip()
        if not parent_message_id:
            raise ValueError(
                "lineage_metadata.parent_message_id is required for non-root messages"
            )


def validate_hims_transition(previous: HIMSMessage, current: HIMSMessage) -> None:
    """Raise when a state transition violates the shadow-mode flow."""

    validate_hims_message(previous)
    validate_hims_message(current)

    if previous.message_id != current.message_id:
        raise ValueError("transitions must keep the same message_id")
    if previous.intent_type != current.intent_type:
        raise ValueError("transitions must keep the same intent_type")
    if previous.status == current.status:
        raise ValueError("transition must change the message status")

    allowed = _ALLOWED_TRANSITIONS.get(previous.intent_type, {}).get(
        previous.status, set()
    )
    if current.status not in allowed:
        raise ValueError(
            f"invalid transition for {previous.intent_type}: "
            f"{previous.status.value} -> {current.status.value}"
        )


__all__ = ["validate_hims_message", "validate_hims_transition"]
