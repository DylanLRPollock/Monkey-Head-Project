"""REST-like API surface description helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

Handler = Callable[[], dict[str, object]]


@dataclass(slots=True)
class ApiRoute:
    path: str
    method: str
    handler: Handler
    metadata: dict[str, object] = field(default_factory=dict)


class ApiSurface:
    """Register serializable route descriptions."""

    def __init__(self) -> None:
        self._routes: list[ApiRoute] = []

    def register(
        self,
        path: str,
        method: str,
        handler: Handler,
        *,
        metadata: dict[str, object] | None = None,
    ) -> ApiRoute:
        route = ApiRoute(path, method, handler, dict(metadata or {}))
        self._routes.append(route)
        return route

    def describe(self) -> list[dict[str, object]]:
        return [
            {
                "path": route.path,
                "method": route.method,
                "metadata": dict(route.metadata),
            }
            for route in self._routes
        ]

    def call(self, path: str, method: str = "GET") -> dict[str, object]:
        for route in self._routes:
            if route.path == path and route.method == method:
                return route.handler()
        raise KeyError(f"Unknown route {method} {path}")


__all__ = ["ApiRoute", "ApiSurface"]
