"""Canonical media command locations and legacy module-identity tests."""

from __future__ import annotations

from importlib import import_module, util
from pathlib import Path

from huey.connectors.pyhuey.tool_manifest import build_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_legacy_media_imports_alias_canonical_modules() -> None:
    for old, modern in (
        ("check_ffmpeg_environment", "cli_ffmpeg_check"),
        ("prepare_audio_for_transcription", "cli_audio_prepare"),
        ("probe_media", "cli_probe"),
    ):
        assert import_module(f"huey.memory.PY.{old}") is import_module(
            f"huey.media.{modern}"
        )
        assert (ROOT / "scripts" / f"{old}.py").is_file()


def test_pyhuey_manifest_has_real_module_commands() -> None:
    items = {item["name"]: item for item in build_manifest()["tools"]}
    for item in items.values():
        command = item["command"]
        assert command[1] == "-m"
        assert util.find_spec(command[2]) is not None
    assert items["check_ffmpeg_environment"]["read_only"]
    assert not items["prepare_audio_for_transcription"]["read_only"]
    assert items["prepare_audio_for_transcription"]["deferred"]
