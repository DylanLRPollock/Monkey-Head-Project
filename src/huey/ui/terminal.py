"""Terminal-oriented rendering helpers."""

from __future__ import annotations


def render_status_table(payload: dict[str, object]) -> str:
    lines = ["section | value", "--- | ---"]
    for key, value in payload.items():
        lines.append(f"{key} | {value}")
    return "\n".join(lines)


__all__ = ["render_status_table"]
