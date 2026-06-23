"""Tests for GUI child-process launch helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from huey.gui.process import build_gui_process_command, build_gui_process_env


def test_build_gui_process_command_targets_function() -> None:
    command = build_gui_process_command("huey.simple_chat_gui", "run_simple_chat")

    assert command[:2] == [sys.executable, "-c"]
    assert "from huey.simple_chat_gui import run_simple_chat" in command[2]
    assert "_copilot_gui_entry()" in command[2]


def test_build_gui_process_env_prepends_src_path(tmp_path: Path) -> None:
    project_root = tmp_path
    src_path = project_root / "src"
    src_path.mkdir()

    env = build_gui_process_env(
        project_root,
        base_env={"PYTHONPATH": os.pathsep.join(["existing-a", "existing-b"])},
    )

    assert env["PYTHONPATH"].split(os.pathsep) == [
        str(src_path),
        "existing-a",
        "existing-b",
    ]


def test_build_gui_process_env_leaves_missing_src_unchanged(tmp_path: Path) -> None:
    env = build_gui_process_env(tmp_path, base_env={"PYTHONPATH": "existing-only"})

    assert env["PYTHONPATH"] == "existing-only"
