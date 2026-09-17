"""Simple JSON indexing helpers for the shared memory pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from huey.memory.pipeline.ingestion import (
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


def default_index_path() -> Path:
    """Return the default JSON index path."""

    return ensure_subdirectory("INDEX") / "memory-index.json"


def _load_index(path: Path | None = None) -> list[dict[str, object]]:
    selected = path or default_index_path()
    if not selected.exists():
        return []
    return json.loads(selected.read_text(encoding="utf-8"))


def _save_index(records: list[dict[str, object]], path: Path | None = None) -> Path:
    selected = path or default_index_path()
    selected.parent.mkdir(parents=True, exist_ok=True)
    selected.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
    return selected


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

    records = []
    for value in paths:
        record = _ingest_path(Path(value).expanduser().resolve())
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

    base = Path(root).expanduser().resolve() if root else get_memory_path(create=True)
    paths = [
        path
        for path in base.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return build_index(paths, index_path=index_path)


def update_index(
    record: dict[str, object],
    *,
    index_path: Path | None = None,
) -> list[dict[str, object]]:
    """Insert or replace a single record in the JSON index."""

    records = _load_index(index_path)
    path_value = str(record.get("path"))
    updated = [item for item in records if str(item.get("path")) != path_value]
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
            str(record.get("metadata", {}).get("summary", "")),
        ]
        if any(needle in haystack.lower() for haystack in haystacks):
            matches.append(record)
    return matches


__all__ = [
    "build_index",
    "default_index_path",
    "rebuild_index",
    "search_index",
    "update_index",
]
