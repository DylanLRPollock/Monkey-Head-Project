"""Fallback PDF parsing helpers without mandatory external dependencies."""

from __future__ import annotations

import string


def parse_pdf_bytes(payload: bytes) -> dict[str, object]:
    """Extract coarse text from PDF bytes for indexing and previews."""

    text = payload.decode("latin-1", errors="ignore")
    printable = "".join(char if char in string.printable else " " for char in text)
    lines = [line.strip() for line in printable.splitlines() if line.strip()]
    extracted = " ".join(lines)
    return {
        "text": extracted,
        "line_count": len(lines),
        "characters": len(extracted),
    }


__all__ = ["parse_pdf_bytes"]
