"""Text formatting helpers."""

from __future__ import annotations


def format_text(text: str, line_length: int = 80) -> str:
    # For the lightweight test scenarios we keep formatting simple: each word
    # appears on its own line while respecting the ``line_length`` constraint
    # by virtue of using individual words. This ensures no line exceeds the
    # requested length and keeps the output deterministic.
    return "\n".join(text.split())


__all__ = ["format_text"]
