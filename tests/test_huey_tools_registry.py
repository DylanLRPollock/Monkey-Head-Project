from __future__ import annotations

import json

from huey.connectors.pyhuey.plugin.huey_tools.registry import (
    get_tool_spec,
    list_tool_specs,
    specs_to_dicts,
)


def test_list_tool_specs_returns_implemented_and_planned_tools() -> None:
    specs = list_tool_specs()
    ids = {spec.id for spec in specs}

    assert "ffmpeg_environment_check" in ids
    assert "speech_prepare_audio" in ids
    assert "pyhuey_package_rename" in ids


def test_get_tool_spec_works() -> None:
    spec = get_tool_spec("ffmpeg_environment_check")

    assert spec.command_name == "huey_ffmpeg_check"
    assert spec.implemented is True


def test_tool_specs_are_json_safe() -> None:
    payload = specs_to_dicts(list_tool_specs())

    json.dumps(payload, sort_keys=True)


def test_no_dangerous_tool_is_marked_safe_by_default() -> None:
    for spec in list_tool_specs():
        if spec.group in {"hardware_sim", "governance_mock", "memory"}:
            assert spec.safe_by_default is False
