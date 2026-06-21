"""Append-only JSONL run logging for HueyOS V1 proof loops."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


class StructuredRunLog:
    """Append and read structured JSONL audit events."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = Path(log_path)

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Append one event and return the stored record."""

        if not event_type:
            raise ValueError("event_type is required")
        record = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "created_at": datetime.now(UTC).isoformat(),
            "payload": payload,
        }
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def read(self) -> list[dict[str, Any]]:
        """Read all valid JSONL events."""

        if not self.log_path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self.log_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at line {line_number}: {exc}") from exc
        return records


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_path", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    append_parser = subparsers.add_parser("append")
    append_parser.add_argument("event_type")
    append_parser.add_argument("payload_json")
    subparsers.add_parser("read")
    args = parser.parse_args(argv)
    log = StructuredRunLog(args.log_path)
    if args.command == "append":
        payload = json.loads(args.payload_json)
        print(json.dumps(log.append(args.event_type, payload), indent=2, sort_keys=True))
    elif args.command == "read":
        print(json.dumps(log.read(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

