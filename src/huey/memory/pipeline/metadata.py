"""Metadata helpers for files entering HueyOS memory."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from huey.media.media_manager import probe_media


def file_hash(path: str | Path, *, algorithm: str = "sha256") -> str:
    """Return the file hash for a path."""

    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError(target)
    hasher = hashlib.new(algorithm)
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def file_stats(path: str | Path) -> dict[str, object]:
    """Return filesystem metadata for a file."""

    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError(target)
    stat = target.stat()
    return {
        "path": str(target),
        "name": target.name,
        "suffix": target.suffix.lower(),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
    }


def file_summary(path: str | Path, *, max_chars: int = 240) -> str:
    """Return a short summary of a file."""

    target = Path(path).expanduser().resolve()
    suffix = target.suffix.lower()
    if suffix in {".txt", ".md", ".py", ".json", ".yaml", ".yml"}:
        content = target.read_text(encoding="utf-8", errors="replace").strip()
        if suffix == ".json":
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                return content[:max_chars]
            return json.dumps(parsed, sort_keys=True)[:max_chars]
        return content[:max_chars]
    if suffix in {".mp3", ".wav", ".flac", ".m4a", ".mp4", ".mov", ".mkv"}:
        try:
            metadata = probe_media(target)
        except (OSError, RuntimeError, ValueError):
            return f"Media file: {target.name}"
        duration = (
            metadata.duration_seconds
            if metadata.duration_seconds is not None
            else "unknown"
        )
        return f"Media file ({target.name}) duration={duration}"
    return f"Binary file: {target.name}"


def generate_metadata(path: str | Path) -> dict[str, object]:
    """Generate a combined metadata payload for a file."""

    target = Path(path).expanduser().resolve()
    payload = file_stats(target)
    payload["sha256"] = file_hash(target)
    payload["summary"] = file_summary(target)
    return payload


__all__ = ["file_hash", "file_stats", "file_summary", "generate_metadata"]
