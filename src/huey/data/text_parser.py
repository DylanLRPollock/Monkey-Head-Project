"""Plain-text parsing utilities for data processing workflows."""

from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    return [
        part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()
    ]


def token_frequency(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in re.findall(r"[A-Za-z0-9_'-]+", text.lower()):
        counts[token] = counts.get(token, 0) + 1
    return counts


__all__ = ["normalize_text", "split_sentences", "token_frequency"]
