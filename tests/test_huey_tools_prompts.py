from __future__ import annotations

import pytest

from huey.connectors.pyhuey.plugin.huey_tools.prompts import generate_task_prompt


def test_known_task_ids_return_non_empty_prompts() -> None:
    for task_id in (
        "media_manager",
        "ffmpeg_validator",
        "speech_pipeline",
        "video_pipeline",
        "command_center_backend",
        "gui_unification",
        "dependency_security",
        "pyhuey_plugin_bridge",
        "phase_2_5_connector",
        "phase_3_pyhuey_rename",
    ):
        prompt = generate_task_prompt(task_id, target_repo="Monkey-Head-Project")
        assert prompt
        assert "Monkey-Head-Project" in prompt or "PyHuey" in prompt


def test_unknown_task_id_raises_value_error() -> None:
    with pytest.raises(ValueError):
        generate_task_prompt("unknown")


def test_phase_3_prompt_does_not_instruct_changing_monkey_repo() -> None:
    prompt = generate_task_prompt("phase_3_pyhuey_rename")

    assert "PyHuey" in prompt
    assert "Do not instruct changes to Monkey-Head-Project" in prompt


def test_phase_2_5_prompt_does_not_instruct_renaming_package() -> None:
    prompt = generate_task_prompt("phase_2_5_connector")

    assert "do not rename the PyHuey package" in prompt.lower()
