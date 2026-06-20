"""Simple serializable web surface for runtime dashboards."""

from __future__ import annotations

from .interface import InterfaceController


class WebInterface:
    """Return view-model payloads that a web layer can expose."""

    def __init__(self, controller: InterfaceController | None = None) -> None:
        self.controller = controller or InterfaceController()

    def routes(self) -> dict[str, str]:
        return {
            "/": "dashboard",
            "/health": "health summary",
            "/agents": "agent overview",
        }

    def render(self, status: dict[str, object], *, mode: str = "summary") -> dict[str, object]:
        presentation = self.controller.present(status, mode=mode)
        return {
            "routes": self.routes(),
            "presentation": presentation,
        }


__all__ = ["WebInterface"]
