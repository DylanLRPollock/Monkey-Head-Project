"""Utility for updating boolean configuration toggles."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from huey.memory.PY.config_toggle_gui import run_config_toggle_gui


def update_toggle_settings(
    config_path: str | Path, updates: Mapping[str, bool]
) -> None:
    path = Path(config_path)
    current = {}
    if path.exists():
        try:
            current = json.loads(path.read_text())
        except json.JSONDecodeError:
            current = {}

    current.update({k: bool(v) for k, v in updates.items()})
    path.write_text(json.dumps(current, indent=2))


__all__ = ["run_config_toggle_gui", "update_toggle_settings"]
