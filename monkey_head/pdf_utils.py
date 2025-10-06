"""Utilities for handling project PDF documents."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from .function_registry import register_function
from .utils.paths import memory_candidates

BASE_DIR = Path(__file__).resolve().parents[1]


def _iter_pdf_dir_candidates(pdf_dir: str | Path) -> List[Path]:
    """Return candidate directories for ``pdf_dir`` in order of preference."""

    path = Path(pdf_dir)
    candidates: List[Path] = [path]
    if path.is_absolute():
        return candidates

    project_candidate = BASE_DIR / path
    if project_candidate not in candidates:
        candidates.append(project_candidate)

    parts = path.parts
    if parts and parts[0] in {"memory", "huey"}:
        relative = Path(*parts[1:]) if len(parts) > 1 else Path()
    else:
        relative = path

    for base in memory_candidates():
        candidate = base / relative
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _default_pdf_candidates() -> List[Path]:
    return [candidate / "PDF" for candidate in memory_candidates()]


def _resolve_pdf_dir(pdf_dir: str | Path) -> Optional[Path]:
    """Return the first existing directory among the candidate paths."""

    for candidate in _iter_pdf_dir_candidates(pdf_dir):
        if candidate.is_dir():
            return candidate
    return None


@register_function
def list_available_pdfs(pdf_dir: Optional[str | Path] = None) -> List[str]:
    """Return a sorted list of PDF filenames in ``pdf_dir``."""

    if pdf_dir is None:
        env = os.environ.get("PDF_DIR")
        if env:
            pdf_dir = Path(env)
        else:
            candidates = _default_pdf_candidates()
            for candidate in candidates:
                if candidate.is_dir():
                    pdf_dir = candidate
                    break
            else:
                pdf_dir = candidates[0]

    resolved = _resolve_pdf_dir(pdf_dir)
    if resolved is None:
        return []
    return sorted(p.name for p in resolved.glob("*.pdf"))


@register_function
def find_pdf(filename: str, pdf_dir: Optional[str | Path] = None) -> Optional[Path]:
    """Return the path to ``filename`` within ``pdf_dir`` if it exists."""

    if pdf_dir is None:
        env = os.environ.get("PDF_DIR")
        if env:
            pdf_dir = Path(env)
        else:
            for candidate in _default_pdf_candidates():
                if candidate.is_dir():
                    pdf_dir = candidate
                    break
            else:
                pdf_dir = _default_pdf_candidates()[0]
    for directory in _iter_pdf_dir_candidates(pdf_dir):
        candidate = directory / filename
        if candidate.is_file():
            return candidate
    return None
