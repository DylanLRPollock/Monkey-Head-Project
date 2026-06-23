"""Dashboard composition helpers."""

from __future__ import annotations

from huey.constants import DEFAULT_DASHBOARD_SECTIONS


def build_dashboard(status: dict[str, object]) -> list[dict[str, object]]:
    cards: list[dict[str, object]] = []
    for section in DEFAULT_DASHBOARD_SECTIONS:
        cards.append(
            {
                "section": section,
                "value": status.get(section, "unavailable"),
            }
        )
    return cards


__all__ = ["build_dashboard"]
