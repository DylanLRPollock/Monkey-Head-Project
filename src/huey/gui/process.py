"""Helpers for launching GUI child processes without blocking the main window."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Mapping


def build_gui_process_command(
    module_name: str,
    function_name: str,
    *,
    python_executable: str | None = None,
) -> list[str]:
    """Return a Python command that imports and launches a GUI function."""

    executable = python_executable or sys.executable
    script = (
        f"from {module_name} import {function_name} as _copilot_gui_entry; "
        "_copilot_gui_entry()"
    )
    return [executable, "-c", script]


def build_gui_process_env(
    project_root: str | Path,
    *,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return environment variables with the local ``src`` path prepended."""

    env = dict(base_env or os.environ)
    src_path = Path(project_root) / "src"
    if not src_path.is_dir():
        return env

    current = env.get("PYTHONPATH", "")
    paths = [entry for entry in current.split(os.pathsep) if entry]
    src_text = str(src_path)
    if src_text not in paths:
        paths.insert(0, src_text)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


__all__ = ["build_gui_process_command", "build_gui_process_env"]
