"""Utilities for handling project PDF documents."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import os
from .function_registry import register_function


@register_function
def list_available_pdfs(pdf_dir: Optional[str | Path] = None) -> List[str]:
    """Return a sorted list of PDF filenames in ``pdf_dir``.

    ``pdf_dir`` defaults to the directory specified by the ``PDF_DIR``
    environment variable or ``"memory/PDF"`` when the variable is unset.

    Parameters
    ----------
    pdf_dir:
        Directory to scan for ``.pdf`` files. When ``None`` the default
        location described above is used.
    """
    if pdf_dir is None:
        env = os.environ.get("PDF_DIR")
        pdf_dir = Path(env) if env else Path("memory") / "PDF"
    path = Path(pdf_dir)
    if not path.is_dir():
        return []
    return sorted(p.name for p in path.glob("*.pdf"))


@register_function
def find_pdf(filename: str, pdf_dir: Optional[str | Path] = None) -> Optional[Path]:
    """Return the path to ``filename`` within ``pdf_dir`` if it exists."""
    if pdf_dir is None:
        env = os.environ.get("PDF_DIR")
        pdf_dir = Path(env) if env else Path("memory") / "PDF"
    path = Path(pdf_dir) / filename
    return path if path.is_file() else None
