"""Minimal ``BaseConfig`` compatible with the lightweight plugin shim."""

from __future__ import annotations

from .plugin import BasePlugin


class BaseConfig:
    def __init__(self, plugin: "BasePlugin | None" = None) -> None:
        self.plugin = plugin

    def from_defaults(self, plugin: "BasePlugin | None" = None) -> None:
        return None

__all__ = ["BaseConfig", "BasePlugin"]
