"""Utilities for handling project PDF documents."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from .function_registry import register_function

BASE_DIR = Path(__file__).resolve().parents[1]


def _iter_pdf_dir_candidates(pdf_dir: str | Path) -> List[Path]:
    """Return candidate directories for ``pdf_dir`` in order of preference."""

    path = Path(pdf_dir)
    candidates: List[Path] = [path]
    if not path.is_absolute():
        candidates.append(BASE_DIR / path)
        if path.parts and path.parts[0] != "huey":
            candidates.append(BASE_DIR / "huey" / path)
    return candidates


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
            for candidate in (
                BASE_DIR / "memory" / "PDF",
                BASE_DIR / "huey" / "memory" / "PDF",
            ):
                if candidate.is_dir():
                    pdf_dir = candidate
                    break
            else:
                pdf_dir = BASE_DIR / "memory" / "PDF"

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
            candidates = [BASE_DIR / "memory" / "PDF", BASE_DIR / "huey" / "memory" / "PDF"]
            for candidate in candidates:
                if candidate.is_dir():
                    pdf_dir = candidate
                    break
            else:
                pdf_dir = candidates[0]
    for directory in _iter_pdf_dir_candidates(pdf_dir):
        candidate = directory / filename
        if candidate.is_file():
            return candidate
    return None
