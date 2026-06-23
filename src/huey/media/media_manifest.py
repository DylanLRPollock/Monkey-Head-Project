"""JSON-safe media manifest models and helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    """Return a stable UTC timestamp for manifests and logs."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class MediaProbe:
    """A compact, JSON-safe summary of ffprobe media metadata."""

    path: str
    format_name: str | None = None
    duration_seconds: float | None = None
    bit_rate: int | None = None
    streams: list[dict[str, Any]] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dictionary."""

        return asdict(self)


@dataclass(frozen=True)
class MediaArtifact:
    """A derived file produced from a source media file."""

    kind: str
    path: str
    role: str
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dictionary."""

        return asdict(self)


@dataclass(frozen=True)
class MediaManifest:
    """Audit manifest for media preparation and preview operations."""

    source_path: str
    operation: str
    created_at: str = field(default_factory=utc_now_iso)
    probe: MediaProbe | None = None
    artifacts: list[MediaArtifact] = field(default_factory=list)
    commands: list[list[str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dictionary."""

        return asdict(self)

    def to_json_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dictionary."""

        return self.to_dict()

    def write_json(self, path: str | Path, *, overwrite: bool = False) -> Path:
        """Write the manifest to ``path`` without overwriting by default."""

        output_path = Path(path)
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"Manifest already exists: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return output_path


def read_manifest(path: str | Path) -> dict[str, Any]:
    """Read a manifest JSON file as a dictionary."""

    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


__all__ = [
    "MediaArtifact",
    "MediaManifest",
    "MediaProbe",
    "read_manifest",
    "utc_now_iso",
]
