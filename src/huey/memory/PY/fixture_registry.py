"""JSON fixture registry for known HueyOS V1 proof-loop inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FixtureRecord:
    """Metadata for a known proof-loop fixture."""

    fixture_id: str
    path: Path
    kind: str
    sha256: str
    size_bytes: int
    registered_at: str
    notes: str = ""

    def to_json_dict(self) -> dict[str, Any]:
        """Return record as JSON-safe data."""

        return {
            "fixture_id": self.fixture_id,
            "path": str(self.path),
            "kind": self.kind,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "registered_at": self.registered_at,
            "notes": self.notes,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, Any]) -> FixtureRecord:
        """Load a fixture record from JSON data."""

        return cls(
            fixture_id=str(data["fixture_id"]),
            path=Path(data["path"]),
            kind=str(data["kind"]),
            sha256=str(data["sha256"]),
            size_bytes=int(data["size_bytes"]),
            registered_at=str(data["registered_at"]),
            notes=str(data.get("notes", "")),
        )


class FixtureRegistry:
    """Read/write JSON registry for immutable fixture references."""

    def __init__(self, registry_path: Path) -> None:
        self.registry_path = Path(registry_path)

    def load(self) -> dict[str, FixtureRecord]:
        """Load all fixture records."""

        if not self.registry_path.exists():
            return {}
        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        return {
            fixture_id: FixtureRecord.from_json_dict(record)
            for fixture_id, record in data.get("fixtures", {}).items()
        }

    def save(self, records: dict[str, FixtureRecord], *, overwrite: bool = True) -> None:
        """Persist fixture records as sorted JSON."""

        if self.registry_path.exists() and not overwrite:
            raise FileExistsError(f"Registry exists and overwrite is false: {self.registry_path}")
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "schema": "huey.v1.fixture_registry",
            "updated_at": datetime.now(UTC).isoformat(),
            "fixtures": {
                key: records[key].to_json_dict()
                for key in sorted(records)
            },
        }
        self.registry_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def register(
        self,
        fixture_id: str,
        path: Path,
        *,
        kind: str = "audio",
        notes: str = "",
        overwrite: bool = False,
    ) -> FixtureRecord:
        """Register one existing fixture file."""

        if not fixture_id:
            raise ValueError("fixture_id is required")
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Fixture file not found: {path}")
        records = self.load()
        if fixture_id in records and not overwrite:
            raise ValueError(f"Fixture already registered: {fixture_id}")
        record = FixtureRecord(
            fixture_id=fixture_id,
            path=path,
            kind=kind,
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
            registered_at=datetime.now(UTC).isoformat(),
            notes=notes,
        )
        records[fixture_id] = record
        self.save(records)
        return record

    def get(self, fixture_id: str) -> FixtureRecord:
        """Return one fixture record or raise KeyError."""

        records = self.load()
        return records[fixture_id]


def sha256_file(path: Path) -> str:
    """Return SHA-256 for a fixture file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("fixture_id")
    add_parser.add_argument("path", type=Path)
    add_parser.add_argument("--kind", default="audio")
    add_parser.add_argument("--notes", default="")
    add_parser.add_argument("--overwrite", action="store_true")
    subparsers.add_parser("list")
    args = parser.parse_args(argv)
    registry = FixtureRegistry(args.registry)
    if args.command == "add":
        record = registry.register(
            args.fixture_id,
            args.path,
            kind=args.kind,
            notes=args.notes,
            overwrite=args.overwrite,
        )
        print(json.dumps(record.to_json_dict(), indent=2, sort_keys=True))
    elif args.command == "list":
        print(json.dumps({k: v.to_json_dict() for k, v in registry.load().items()}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

