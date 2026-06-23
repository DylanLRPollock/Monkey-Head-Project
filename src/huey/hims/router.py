"""Route HIMS messages into filesystem-first ThunderMail mailboxes."""

from __future__ import annotations

from enum import StrEnum

from huey.hims.schema import HIMSMessage, MessageStatus


class Mailbox(StrEnum):
    """Mailbox layout for the shadow-mode HIMS slice."""

    INBOX = "inbox"
    OUTBOX = "outbox"
    PENDING_VALIDATION = "pending_validation"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    ARCHIVED = "archived"


MAILBOXES = tuple(Mailbox)


def _default_mailbox(status: MessageStatus) -> Mailbox:
    if status == MessageStatus.QUEUED:
        return Mailbox.PENDING_VALIDATION
    if status == MessageStatus.ACCEPTED:
        return Mailbox.APPROVED
    if status == MessageStatus.REJECTED:
        return Mailbox.REJECTED
    if status in {
        MessageStatus.DELIVERED,
        MessageStatus.OPENED,
        MessageStatus.EXECUTING,
        MessageStatus.EXECUTED,
        MessageStatus.LOGGED,
    }:
        return Mailbox.EXECUTED
    if status == MessageStatus.ARCHIVED:
        return Mailbox.ARCHIVED
    return Mailbox.OUTBOX


def mailbox_for(message: HIMSMessage) -> Mailbox:
    """Return the mailbox that should hold the current message snapshot."""

    if message.intent_type == "external_interface_packet":
        if message.status == MessageStatus.ARCHIVED:
            return Mailbox.ARCHIVED
        return Mailbox.INBOX
    if message.intent_type == "request":
        return _default_mailbox(message.status)
    if message.intent_type in {"report", "alert"}:
        if message.status == MessageStatus.ARCHIVED:
            return Mailbox.ARCHIVED
        return Mailbox.EXECUTED
    if message.intent_type == "archived_record":
        return Mailbox.ARCHIVED
    return _default_mailbox(message.status)


__all__ = ["MAILBOXES", "Mailbox", "mailbox_for"]
