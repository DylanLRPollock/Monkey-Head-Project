# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: App module (huey/pygpt_net)

"""Stub application runner compatible with Monkey Head integration tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Iterable

_LAST_LAUNCH_STATE: dict[str, object] = {"tool_count": 0, "tools": []}


def _action_label(action: object) -> str | None:
    value = getattr(action, "text", None)
    if callable(value):
        value = value()
    if value is None:
        return None
    return str(value)


def run(*, tools: Iterable[object] | None = None) -> dict[str, object]:
    """Simulate launching the PyGPT GUI with the provided tools."""

    launched_tools: list[dict[str, object]] = []
    for tool in tools or ():
        menu: dict[str, object] = {}
        setup = getattr(tool, "setup_menu", None)
        if callable(setup):
            configured = setup()
            if isinstance(configured, dict):
                menu = configured
        payload = None
        gui_payload = getattr(tool, "gui_payload", None)
        if callable(gui_payload):
            payload = gui_payload()
        launched_tools.append(
            {
                "id": getattr(tool, "id", tool.__class__.__name__),
                "class_name": tool.__class__.__name__,
                "module": tool.__class__.__module__,
                "menu_actions": sorted(menu),
                "menu_labels": {
                    action_id: (_action_label(action) or action_id)
                    for action_id, action in menu.items()
                },
                "gui_payload": payload,
            }
        )
    global _LAST_LAUNCH_STATE
    _LAST_LAUNCH_STATE = {
        "tool_count": len(launched_tools),
        "tools": launched_tools,
    }
    return get_last_launch_state()


def get_last_launch_state() -> dict[str, object]:
    """Return the last captured GUI launch state."""

    return deepcopy(_LAST_LAUNCH_STATE)


def reset_last_launch_state() -> None:
    """Clear the captured GUI launch state."""

    global _LAST_LAUNCH_STATE
    _LAST_LAUNCH_STATE = {"tool_count": 0, "tools": []}


__all__ = ["get_last_launch_state", "reset_last_launch_state", "run"]
