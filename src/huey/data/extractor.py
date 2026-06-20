"""Structured extraction helpers for semi-structured documents."""

from __future__ import annotations

from .text_parser import split_sentences


def extract_key_values(text: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key:
            pairs[key] = value
    return pairs


def extract_sections(text: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    for block in text.split("\n\n"):
        stripped = block.strip()
        if not stripped:
            continue
        first_line, *_ = stripped.splitlines()
        sections.append(
            {
                "title": first_line[:80],
                "content": stripped,
                "sentences": split_sentences(stripped),
            }
        )
    return sections


__all__ = ["extract_key_values", "extract_sections"]
