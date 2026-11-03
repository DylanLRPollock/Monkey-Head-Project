"""Simple JSON indexing helpers for the shared memory pipeline."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from huey.memory.ingestion import (
    ingest_audio,
    ingest_json,
    ingest_md,
    ingest_pdf,
    ingest_txt,
    ingest_video,
)
from huey.utils.paths import ensure_subdirectory, get_memory_path

SUPPORTED_EXTENSIONS = {
    ".txt": ingest_txt,
    ".md": ingest_md,
    ".json": ingest_json,
    ".pdf": ingest_pdf,
    ".mp3": ingest_audio,
    ".wav": ingest_audio,
    ".flac": ingest_audio,
    ".m4a": ingest_audio,
    ".mp4": ingest_video,
    ".mov": ingest_video,
    ".mkv": ingest_video,
}


def default_index_path(*, create: bool = True) -> Path:
    """Return the memory index location without requiring a side effect."""
    if create:
        return ensure_subdirectory("INDEX") / "memory-index.json"
    return get_memory_path(create=False) / "INDEX" / "memory-index.json"


def _load_index(path: Path | None = None) -> list[dict[str, object]]:
    selected = Path(path) if path is not None else default_index_path(create=False)
    if not selected.exists():
        return []
    records = json.loads(selected.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ValueError(f"Malformed memory index (expected list of objects): {selected}")
    return records


def _save_index(records: list[dict[str, object]], path: Path | None = None) -> Path:
    selected = Path(path) if path is not None else default_index_path()
    selected.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(records, indent=2, sort_keys=True, ensure_ascii=False)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=selected.parent,
            prefix=f".{selected.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, selected)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return selected


_SKIP_DIRECTORIES = {"PY", "INDEX", "__pycache__", ".git", ".venv", "node_modules"}


def discover_paths(root: str | Path, *, index_path: Path | None = None) -> list[Path]:
    """Discover memory data without following symlinks or indexing internal code."""
    base = Path(root).expanduser().resolve()
    if not base.is_dir():
        raise NotADirectoryError(f"Memory index root is not a directory: {base}")
    excluded = Path(index_path).expanduser().resolve() if index_path else None
    found: list[Path] = []
    for path in base.rglob("*"):
        relative = path.relative_to(base)
        if any(part in _SKIP_DIRECTORIES or part.startswith(".") for part in relative.parts):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        if excluded is not None and path.resolve() == excluded:
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            found.append(path)
    return sorted(found)


def _ingest_path(path: Path) -> dict[str, object] | None:
    handler = SUPPORTED_EXTENSIONS.get(path.suffix.lower())
    if handler is None:
        return None
    return handler(path, store_copy=False)


def build_index(
    paths: list[str | Path],
    *,
    index_path: Path | None = None,
) -> list[dict[str, object]]:
    """Build an index from explicit file paths."""

    excluded = (
        Path(index_path).expanduser().resolve()
        if index_path else default_index_path(create=False).resolve()
    )
    records = []
    for value in paths:
        path = Path(value).expanduser()
        if path.is_symlink():
            continue
        source = path.resolve()
        if source == excluded:
            continue
        record = _ingest_path(source)
        if record is not None:
            records.append(record)
    _save_index(records, index_path)
    return records


def rebuild_index(
    root: str | Path | None = None,
    *,
    index_path: Path | None = None,
) -> list[dict[str, object]]:
    """Rebuild the index by walking a memory root."""

    base = (
        Path(root).expanduser().resolve()
        if root is not None else get_memory_path(create=False)
    )
    return build_index(discover_paths(base, index_path=index_path), index_path=index_path)


def update_index(
    record: dict[str, object],
    *,
    index_path: Path | None = None,
) -> list[dict[str, object]]:
    """Insert or replace a single record in the JSON index."""

    records = _load_index(index_path)
    path_value = record.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise ValueError("Index record requires a nonempty 'path' string")
    updated = [item for item in records if item.get("path") != path_value]
    updated.append(record)
    _save_index(updated, index_path)
    return updated


def search_index(
    query: str,
    *,
    index_path: Path | None = None,
) -> list[dict[str, object]]:
    """Search the index for a query string across paths, summaries, and content."""

    needle = query.strip().lower()
    if not needle:
        return []
    matches = []
    for record in _load_index(index_path):
        haystacks = [
            str(record.get("path", "")),
            str(record.get("kind", "")),
            str(record.get("content", "")),
            str(record.get("metadata", {}).get("summary", ""))
            if isinstance(record.get("metadata"), dict) else "",
        ]
        if any(needle in haystack.lower() for haystack in haystacks):
            matches.append(record)
    return matches


__all__ = [
    "build_index",
    "default_index_path",
    "discover_paths",
    "rebuild_index",
    "search_index",
    "update_index",
]
