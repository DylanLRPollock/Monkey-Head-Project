"""Utilities for handling project PDF documents."""

from __future__ import annotations

from pathlib import Path
from typing import List


def list_available_pdfs(pdf_dir: str | Path = Path("memory") / "PDF") -> List[str]:
    """Return a sorted list of PDF filenames in ``pdf_dir``.

    Parameters
    ----------
    pdf_dir:
        Directory to scan for ``.pdf`` files.
    """
    path = Path(pdf_dir)
    if not path.is_dir():
        return []
    return sorted(p.name for p in path.glob("*.pdf"))
