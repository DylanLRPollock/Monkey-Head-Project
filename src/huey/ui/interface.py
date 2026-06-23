"""Main UI controller for terminal and web projections."""

from __future__ import annotations

from .adaptive_ui import AdaptiveUIEngine
from .dashboard import build_dashboard
from .terminal import render_status_table


class InterfaceController:
    """Prepare the same runtime state for multiple presentation layers."""

    def __init__(self) -> None:
        self.adaptive = AdaptiveUIEngine()

    def present(
        self, status: dict[str, object], *, mode: str = "summary"
    ) -> dict[str, object]:
        profile = self.adaptive.choose(mode=mode)
        return {
            "profile": profile,
            "dashboard": build_dashboard(status),
            "terminal": render_status_table(status),
        }


__all__ = ["InterfaceController"]
