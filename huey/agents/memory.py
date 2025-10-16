# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Memory module (huey/agents)

"""Utilities for persisting agent state within the honeycomb memory."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from monkey_head.honeycomb_storage import HoneycombRecord, HoneycombStorage


@dataclass(frozen=True)
class MemoryEntry:
    """A single memory entry persisted for an agent."""

    key: str
    topic: str
    payload: Dict[str, Any]
    created_at: float
    updated_at: float


class AgentMemory:
    """High level helper around :class:`HoneycombStorage` for agents."""

    def __init__(self, storage: HoneycombStorage, agent_id: str) -> None:
        self._storage = storage
        self._agent_id = agent_id

    # ------------------------------------------------------------------
    # General purpose memory helpers
    # ------------------------------------------------------------------
    def remember(self, topic: str, payload: Dict[str, Any]) -> MemoryEntry:
        """Persist ``payload`` associated with ``topic``."""

        key = f"agent/{self._agent_id}/{topic}/{uuid.uuid4().hex}"
        record = self._storage.store(key, payload)
        return MemoryEntry(
            key=record.key,
            topic=topic,
            payload=payload,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def recall(self, topic: str, *, limit: Optional[int] = None) -> List[MemoryEntry]:
        """Return recent entries for ``topic`` ordered from newest to oldest."""

        prefix = f"agent/{self._agent_id}/{topic}/"
        records = self._storage.query(prefix, limit=limit)
        entries: List[MemoryEntry] = []
        for record in records:
            entries.append(
                MemoryEntry(
                    key=record.key,
                    topic=topic,
                    payload=record.data,
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                )
            )
        return entries

    def log_conversation(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> HoneycombRecord:
        """Record a conversational turn for transparency."""

        metadata = metadata.copy() if metadata else {}
        metadata.setdefault("agent_id", self._agent_id)
        return self._storage.append_conversation(
            conversation_id,
            role=role,
            content=content,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def last_decisions(self, limit: int = 5) -> List[MemoryEntry]:
        """Shortcut for retrieving the most recent decision payloads."""

        return self.recall("decision", limit=limit)


__all__ = ["AgentMemory", "MemoryEntry"]
