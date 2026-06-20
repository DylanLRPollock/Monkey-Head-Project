"""Explicit adapters for legacy Tkinter GUI modules."""

from __future__ import annotations

from importlib import import_module
from importlib.util import find_spec


def legacy_license_gui_available() -> bool:
    """Return ``True`` if the legacy license GUI can be imported."""

    return find_spec("huey.memory.PY.license_gui") is not None


def legacy_ai_tools_gui_available() -> bool:
    """Return ``True`` if the legacy AI tools GUI can be imported."""

    return find_spec("huey.memory.PY.ai_tools_gui") is not None


def launch_legacy_license_gui(config_path: str | None = None) -> None:
    """Launch the legacy Tkinter license GUI explicitly."""

    module = import_module("huey.memory.PY.license_gui")
    if config_path is None:
        module.show_license_gui()
        return
    module.show_license_gui(config_path)


def launch_legacy_ai_tools_gui() -> None:
    """Launch the legacy AI tools GUI explicitly."""

    module = import_module("huey.memory.PY.ai_tools_gui")
    module.run_ai_tools()


def legacy_gui_status() -> dict[str, bool]:
    """Return availability status for legacy GUI tools."""

    return {
        "license_gui": legacy_license_gui_available(),
        "ai_tools_gui": legacy_ai_tools_gui_available(),
    }


__all__ = [
    "launch_legacy_ai_tools_gui",
    "launch_legacy_license_gui",
    "legacy_ai_tools_gui_available",
    "legacy_gui_status",
    "legacy_license_gui_available",
]
