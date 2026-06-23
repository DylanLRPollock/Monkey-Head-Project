"""Filesystem-first ThunderMail delivery helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from huey.hims.schema import HIMSMessage, MessageStatus
from huey.hims.storage import HIMSStorage


class ThunderMail:
    """Deliver and transition shadow-mode HIMS messages."""

    def __init__(self, root: Path) -> None:
        self.storage = HIMSStorage(root)

    @property
    def root(self) -> Path:
        return self.storage.root

    @property
    def ledger_path(self) -> Path:
        return self.storage.ledger.ledger_path

    def post(
        self,
        message: HIMSMessage,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist a new message snapshot."""

        return self.storage.write_message(message, metadata=metadata)

    def transition(
        self,
        message_id: str,
        *,
        status: MessageStatus,
        reason: str | None = None,
        payload_updates: dict[str, Any] | None = None,
        signature_updates: dict[str, Any] | None = None,
        lineage_updates: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Transition one stored message into a new state."""

        return self.storage.transition_message(
            message_id,
            status=status,
            reason=reason,
            payload_updates=payload_updates,
            signature_updates=signature_updates,
            lineage_updates=lineage_updates,
        )

    def read_message(self, message_id: str) -> dict[str, Any] | None:
        """Return one current message snapshot."""

        return self.storage.read_message(message_id)

    def read_ledger(self) -> list[dict[str, Any]]:
        """Return the append-only ledger entries."""

        return self.storage.read_ledger()


__all__ = ["ThunderMail"]
