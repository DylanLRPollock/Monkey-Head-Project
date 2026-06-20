"""Small fallback ``BasePlugin`` used in the repository-local PyHuey shim."""

from __future__ import annotations

from typing import Any


class BasePlugin:
    """Store plugin metadata and simple option values."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.window = kwargs.get("window")
        self.id = ""
        self.name = ""
        self.description = ""
        self.prefix = ""
        self.type: list[str] = []
        self.order = 0
        self.use_locale = False
        self._options: dict[str, dict[str, Any]] = {}
        self._option_values: dict[str, Any] = {}

    def add_option(self, key: str, **kwargs: Any) -> None:
        self._options[key] = dict(kwargs)
        self._option_values[key] = kwargs.get("value")

    def get_option_value(self, key: str, default: Any = None) -> Any:
        return self._option_values.get(key, default)

    def set_option_value(self, key: str, value: Any) -> None:
        self._option_values[key] = value

    def init_options(self) -> None:  # pragma: no cover - hook for subclasses
        return None

    def setup_menu(self) -> dict[str, object]:
        return {}

    def handle(self, event: object, *args: Any, **kwargs: Any) -> object | None:
        return None


__all__ = ["BasePlugin"]
