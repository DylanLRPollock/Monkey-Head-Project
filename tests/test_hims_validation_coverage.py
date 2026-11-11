"""Exercise HIMS message and transition validation rules."""

from __future__ import annotations

import pytest

from huey.hims.schema import HIMSMessage, MessageStatus
from huey.hims.validation import validate_hims_message, validate_hims_transition


def _message(
    *,
    intent: str = "request",
    status: MessageStatus = MessageStatus.QUEUED,
    message_id: str = "message-1",
    sender: str = "sender",
    recipient: str = "recipient",
    role_context: str = "operator",
    authority_requirement: str = "authorized",
    route: list[str] | None = None,
    lineage: dict[str, str] | None = None,
) -> HIMSMessage:
    return HIMSMessage(
        message_id=message_id,
        sender=sender,
        recipient=recipient,
        role_context=role_context,
        intent_type=intent,
        authority_requirement=authority_requirement,
        status=status,
        route=["sender", "recipient"] if route is None else route,
        lineage_metadata=(
            {"root_lineage_id": "root-1", "parent_message_id": "parent-1"}
            if lineage is None
            else lineage
        ),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sender", " "),
        ("recipient", ""),
        ("role_context", "\t"),
        ("intent_type", ""),
        ("authority_requirement", "  "),
    ],
)
def test_message_requires_nonblank_identity_fields(field, value):
    with pytest.raises(ValueError, match=f"message {field} is required"):
        name = "intent" if field == "intent_type" else field
        validate_hims_message(_message(**{name: value}))


def test_message_rejects_empty_route_unsupported_intent_and_invalid_status():
    with pytest.raises(ValueError, match="route must contain at least one step"):
        validate_hims_message(_message(route=[]))

    with pytest.raises(ValueError, match="unsupported intent_type: unknown"):
        validate_hims_message(_message(intent="unknown"))

    with pytest.raises(ValueError, match="status draft is not valid for request"):
        validate_hims_message(_message(status=MessageStatus.DRAFT))


def test_lineage_requires_root_and_parent_except_for_external_root_packet():
    with pytest.raises(ValueError, match="root_lineage_id is required"):
        validate_hims_message(_message(lineage={"parent_message_id": "parent"}))

    with pytest.raises(ValueError, match="parent_message_id is required"):
        validate_hims_message(_message(lineage={"root_lineage_id": "root"}))

    packet = _message(
        intent="external_interface_packet",
        status=MessageStatus.ACCEPTED,
        lineage={"root_lineage_id": "root"},
    )
    validate_hims_message(packet)

    archived = _message(
        intent="archived_record",
        status=MessageStatus.ARCHIVED,
    )
    validate_hims_message(archived)


def test_transition_requires_stable_identity_intent_and_changed_status():
    previous = _message()
    with pytest.raises(ValueError, match="same message_id"):
        validate_hims_transition(previous, _message(message_id="other"))

    with pytest.raises(ValueError, match="same intent_type"):
        validate_hims_transition(
            previous,
            _message(intent="report", status=MessageStatus.EXECUTED),
        )

    with pytest.raises(ValueError, match="must change the message status"):
        validate_hims_transition(previous, previous)

    with pytest.raises(ValueError, match="invalid transition for request"):
        validate_hims_transition(
            previous,
            _message(status=MessageStatus.ARCHIVED),
        )


@pytest.mark.parametrize(
    ("intent", "before", "after"),
    [
        ("external_interface_packet", MessageStatus.ACCEPTED, MessageStatus.ARCHIVED),
        ("request", MessageStatus.QUEUED, MessageStatus.ACCEPTED),
        ("request", MessageStatus.QUEUED, MessageStatus.REJECTED),
        ("request", MessageStatus.ACCEPTED, MessageStatus.EXECUTING),
        ("request", MessageStatus.ACCEPTED, MessageStatus.EXECUTED),
        ("request", MessageStatus.ACCEPTED, MessageStatus.ARCHIVED),
        ("request", MessageStatus.EXECUTING, MessageStatus.EXECUTED),
        ("request", MessageStatus.EXECUTING, MessageStatus.REJECTED),
        ("request", MessageStatus.EXECUTED, MessageStatus.ARCHIVED),
        ("request", MessageStatus.REJECTED, MessageStatus.ARCHIVED),
        ("report", MessageStatus.EXECUTED, MessageStatus.ARCHIVED),
        ("alert", MessageStatus.EXECUTED, MessageStatus.ARCHIVED),
    ],
)
def test_valid_transitions_for_each_intent(intent, before, after):
    lineage = (
        {"root_lineage_id": "root-1"}
        if intent == "external_interface_packet"
        else {"root_lineage_id": "root-1", "parent_message_id": "parent-1"}
    )
    validate_hims_transition(
        _message(intent=intent, status=before, lineage=lineage),
        _message(intent=intent, status=after, lineage=lineage),
    )
