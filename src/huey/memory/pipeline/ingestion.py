"""Unified ingestion helpers for common memory inputs."""

from __future__ import annotations

import json
from pathlib import Path
from shutil import copy2

from huey.media.media_manager import probe_media
from huey.memory.pipeline.metadata import generate_metadata
from huey.utils.paths import ensure_subdirectory


def _store_copy(source: Path, category: str) -> Path:
    target_dir = ensure_subdirectory("INGESTED", category.upper())
    target_path = target_dir / source.name
    copy2(source, target_path)
    return target_path


def ingest_txt(path: str | Path, *, store_copy: bool = True) -> dict[str, object]:
    """Ingest a plain-text file into the memory pipeline."""

    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    stored_path = _store_copy(source, "txt") if store_copy else source
    return {
        "kind": "txt",
        "path": str(stored_path),
        "content": stored_path.read_text(encoding="utf-8", errors="replace"),
        "metadata": generate_metadata(stored_path),
    }


def ingest_md(path: str | Path, *, store_copy: bool = True) -> dict[str, object]:
    """Ingest a Markdown file."""

    payload = ingest_txt(path, store_copy=store_copy)
    payload["kind"] = "md"
    return payload


def ingest_json(path: str | Path, *, store_copy: bool = True) -> dict[str, object]:
    """Ingest a JSON file."""

    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    stored_path = _store_copy(source, "json") if store_copy else source
    data = json.loads(stored_path.read_text(encoding="utf-8"))
    return {
        "kind": "json",
        "path": str(stored_path),
        "content": data,
        "metadata": generate_metadata(stored_path),
    }


def ingest_pdf(path: str | Path, *, store_copy: bool = True) -> dict[str, object]:
    """Ingest a PDF document, extracting text when a parser is available."""

    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    stored_path = _store_copy(source, "pdf") if store_copy else source
    pages: list[str] = []
    parser = "unavailable"
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(stored_path))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
        parser = "pypdf"
    except ImportError:
        pages = []
    return {
        "kind": "pdf",
        "path": str(stored_path),
        "content": "\n\n".join(page for page in pages if page),
        "page_count": len(pages),
        "parser": parser,
        "metadata": generate_metadata(stored_path),
    }


def ingest_audio(path: str | Path, *, store_copy: bool = True) -> dict[str, object]:
    """Ingest an audio file and capture probe metadata."""

    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    stored_path = _store_copy(source, "audio") if store_copy else source
    return {
        "kind": "audio",
        "path": str(stored_path),
        "probe": probe_media(stored_path),
        "metadata": generate_metadata(stored_path),
    }


def ingest_video(path: str | Path, *, store_copy: bool = True) -> dict[str, object]:
    """Ingest a video file and capture probe metadata."""

    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    stored_path = _store_copy(source, "video") if store_copy else source
    return {
        "kind": "video",
        "path": str(stored_path),
        "probe": probe_media(stored_path),
        "metadata": generate_metadata(stored_path),
    }


__all__ = [
    "ingest_audio",
    "ingest_json",
    "ingest_md",
    "ingest_pdf",
    "ingest_txt",
    "ingest_video",
]
