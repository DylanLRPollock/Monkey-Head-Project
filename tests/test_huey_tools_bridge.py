from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from huey.connectors.pyhuey.plugin.huey_tools.bridge import (
    HueyBridgeConfig,
    HueyToolBridge,
)


def _write_script(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_bridge_constructor_works_without_monkey_path() -> None:
    bridge = HueyToolBridge()
    status = bridge.status()

    assert status["project_path"] is None
    assert status["project_path_exists"] is False


def test_run_script_refuses_missing_project_path() -> None:
    bridge = HueyToolBridge()

    with pytest.raises(RuntimeError):
        bridge.run_script("scripts/check_ffmpeg_environment.py", ["--json"])


def test_run_script_refuses_missing_script(tmp_path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    bridge = HueyToolBridge(HueyBridgeConfig(monkey_head_project_path=project))

    with pytest.raises(FileNotFoundError):
        bridge.run_script("scripts/check_ffmpeg_environment.py", ["--json"])


def test_run_script_uses_list_command_and_no_shell(tmp_path, monkeypatch) -> None:
    project = tmp_path / "project"
    script = project / "scripts" / "check_ffmpeg_environment.py"
    _write_script(script, "print('ok')\n")
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["shell"] = kwargs.get("shell")
        return subprocess.CompletedProcess(
            command, 0, stdout='{"ready": true}', stderr=""
        )

    monkeypatch.setattr(
        "huey.connectors.pyhuey.plugin.huey_tools.bridge.subprocess.run",
        fake_run,
    )

    bridge = HueyToolBridge(HueyBridgeConfig(monkey_head_project_path=project))
    result = bridge.run_script("scripts/check_ffmpeg_environment.py", ["--json"])

    assert isinstance(captured["command"], list)
    assert captured["shell"] is False
    assert result.parsed_json == {"ready": True}


def test_check_ffmpeg_calls_fixed_script_with_json(tmp_path, monkeypatch) -> None:
    project = tmp_path / "project"
    script = project / "scripts" / "check_ffmpeg_environment.py"
    _write_script(script, "print('ok')\n")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"ready": true, "ffmpeg": true}',
            stderr="",
        )

    monkeypatch.setattr(
        "huey.connectors.pyhuey.plugin.huey_tools.bridge.subprocess.run",
        fake_run,
    )

    bridge = HueyToolBridge(HueyBridgeConfig(monkey_head_project_path=project))
    result = bridge.check_ffmpeg(strict=True)

    assert "--json" in result.command
    assert "--strict" in result.command


def test_prepare_audio_calls_fixed_script(tmp_path, monkeypatch) -> None:
    project = tmp_path / "project"
    source = project / "input.wav"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"audio")
    script = project / "scripts" / "prepare_audio_for_transcription.py"
    _write_script(script, "print('ok')\n")

    def fake_run(command, **kwargs):
        payload = {"output_path": str(project / "input.prepared.wav"), "exists": True}
        return subprocess.CompletedProcess(
            command, 0, stdout=json.dumps(payload), stderr=""
        )

    monkeypatch.setattr(
        "huey.connectors.pyhuey.plugin.huey_tools.bridge.subprocess.run",
        fake_run,
    )

    bridge = HueyToolBridge(HueyBridgeConfig(monkey_head_project_path=project))
    result = bridge.prepare_audio(source)

    assert "prepare_audio_for_transcription.py" in " ".join(result.command)
    assert result.parsed_json["exists"] is True


def test_timeout_is_handled_cleanly(tmp_path, monkeypatch) -> None:
    project = tmp_path / "project"
    script = project / "scripts" / "check_ffmpeg_environment.py"
    _write_script(script, "print('ok')\n")

    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, timeout=1.0)

    monkeypatch.setattr(
        "huey.connectors.pyhuey.plugin.huey_tools.bridge.subprocess.run",
        fake_run,
    )

    bridge = HueyToolBridge(HueyBridgeConfig(monkey_head_project_path=project))
    result = bridge.check_ffmpeg()

    assert result.returncode == 124
    assert result.ok is False
