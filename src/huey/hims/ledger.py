"""Append-only JSONL ledger for shadow-mode HIMS events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from huey.hims.schema import json_safe, utc_now


class HIMSLedger:
    """Persist append-only ledger events as JSON lines."""

    def __init__(self, ledger_path: Path) -> None:
        self.ledger_path = Path(ledger_path)

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Append one ledger event and return the stored record."""

        if not event_type:
            raise ValueError("event_type is required")

        record = {
            "event_id": uuid4().hex,
            "event_type": event_type,
            "created_at": utc_now(),
            "payload": json_safe(payload),
        }
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def read(self) -> list[dict[str, Any]]:
        """Read all valid ledger entries from disk."""

        if not self.ledger_path.exists():
            return []

        records: list[dict[str, Any]] = []
        with self.ledger_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid HIMS ledger JSONL at line {line_number}: {exc}"
                    ) from exc
        return records


__all__ = ["HIMSLedger"]
