"""Filesystem-first storage for shadow-mode HIMS records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from huey.hims.ledger import HIMSLedger
from huey.hims.router import MAILBOXES, Mailbox, mailbox_for
from huey.hims.schema import HIMSMessage, MessageStatus, utc_now
from huey.hims.validation import validate_hims_message, validate_hims_transition


class HIMSStorage:
    """Store current message snapshots plus an append-only ledger."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.records_dir = self.root / "records"
        self.ledger = HIMSLedger(self.root / "ledger.jsonl")

        self.root.mkdir(parents=True, exist_ok=True)
        self.records_dir.mkdir(parents=True, exist_ok=True)
        for mailbox in MAILBOXES:
            (self.root / mailbox.value).mkdir(parents=True, exist_ok=True)

    def _record_path(self, message_id: str) -> Path:
        return self.records_dir / f"{message_id}.json"

    def _mailbox_path(self, mailbox: Mailbox | str, message_id: str) -> Path:
        selected = mailbox.value if isinstance(mailbox, Mailbox) else str(mailbox)
        return self.root / selected / f"{message_id}.json"

    def read_message(self, message_id: str) -> dict[str, Any] | None:
        """Return the current stored snapshot for one message."""

        path = self._record_path(message_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def read_ledger(self) -> list[dict[str, Any]]:
        """Return all ledger entries."""

        return self.ledger.read()

    def write_message(
        self,
        message: HIMSMessage,
        *,
        event_type: str = "message.created",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist one message snapshot and append a ledger record."""

        validate_hims_message(message)

        previous = self.read_message(message.message_id)
        previous_mailbox = (
            str(previous.get("current_mailbox")) if previous is not None else None
        )
        current_mailbox = mailbox_for(message).value

        snapshot = message.to_dict(current_mailbox=current_mailbox)
        snapshot["updated_at"] = utc_now()

        self._record_path(message.message_id).write_text(
            json.dumps(snapshot, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        if previous_mailbox and previous_mailbox != current_mailbox:
            old_mailbox_path = self._mailbox_path(previous_mailbox, message.message_id)
            if old_mailbox_path.exists():
                old_mailbox_path.unlink()

        self._mailbox_path(current_mailbox, message.message_id).write_text(
            json.dumps(snapshot, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        self.ledger.append(
            event_type,
            {
                "message_id": message.message_id,
                "intent_type": message.intent_type,
                "status": message.status.value,
                "mailbox": current_mailbox,
                "record": snapshot,
                "metadata": dict(metadata or {}),
            },
        )
        return snapshot

    def transition_message(
        self,
        message_id: str,
        *,
        status: MessageStatus,
        reason: str | None = None,
        payload_updates: dict[str, Any] | None = None,
        signature_updates: dict[str, Any] | None = None,
        lineage_updates: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Load one stored message, transition it, and persist the update."""

        existing = self.read_message(message_id)
        if existing is None:
            raise FileNotFoundError(f"HIMS message not found: {message_id}")

        previous_message = HIMSMessage.from_dict(existing)
        merged_signature_updates = dict(signature_updates or {})
        if reason:
            merged_signature_updates["transition_reason"] = reason

        updated_message = previous_message.with_status(
            status,
            payload_updates=payload_updates,
            signature_updates=merged_signature_updates or None,
            lineage_updates=lineage_updates,
        )
        validate_hims_transition(previous_message, updated_message)
        return self.write_message(
            updated_message,
            event_type="message.transition",
            metadata={"reason": reason} if reason else None,
        )


__all__ = ["HIMSStorage"]
