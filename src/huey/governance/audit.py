"""Audit logging for governance decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time


@dataclass(slots=True)
class AuditEntry:
    action: str
    approved: bool
    rationale: str
    metadata: dict[str, object] = field(default_factory=dict)
    timestamp: float = field(default_factory=time)


class AuditLog:
    """Append-only in-memory audit log."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def record(
        self,
        action: str,
        *,
        approved: bool,
        rationale: str,
        metadata: dict[str, object] | None = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            action=action,
            approved=approved,
            rationale=rationale,
            metadata=dict(metadata or {}),
        )
        self._entries.append(entry)
        return entry

    def entries(self) -> list[AuditEntry]:
        return list(self._entries)

    def snapshot(self) -> list[dict[str, object]]:
        return [
            {
                "action": entry.action,
                "approved": entry.approved,
                "rationale": entry.rationale,
                "metadata": dict(entry.metadata),
                "timestamp": entry.timestamp,
            }
            for entry in self._entries
        ]


__all__ = ["AuditEntry", "AuditLog"]
