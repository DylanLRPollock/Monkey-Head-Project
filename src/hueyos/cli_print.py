"""Minimal message printer used for CLI output."""

from __future__ import annotations

LEVELS = {
    "info": "INFO",
    "warning": "WARNING",
    "error": "ERROR",
}


def print_message(message: str, level: str = "info") -> None:
    level_key = level.lower()
    if level_key not in LEVELS:
        raise ValueError(f"Unsupported level: {level}")
    label = LEVELS[level_key]
    print(f"[{label}] {message}")


__all__ = ["print_message"]
