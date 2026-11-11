from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

from huey.pyhuey_integration import prepare_pygpt, reset_pygpt_state


def test_plugin_import_does_not_require_external_checkout() -> None:
    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    module = importlib.import_module("pygpt_net.plugin.huey_tools")

    assert hasattr(module, "Plugin")
    assert hasattr(module, "HueyToolBridge")


def test_plugin_metadata_and_commands_exist() -> None:
    from huey.connectors.pyhuey.item.ctx import CtxItem
    from huey.connectors.pyhuey.plugin.huey_tools.plugin import Plugin

    plugin = Plugin()
    command_names = {item["cmd"] for item in plugin.cmd_syntax({})}
    result = plugin.cmd(CtxItem(), [{"cmd": "huey_safety_policy", "params": {}}])

    assert plugin.id == "huey_tools"
    assert plugin.name == "Huey Tools"
    assert "huey_status" in command_names
    assert "huey_ffmpeg_check" in command_names
    assert result[0]["ok"] is True


def test_plugin_dispatches_all_safe_commands_and_attaches_context(monkeypatch) -> None:
    from huey.connectors.pyhuey.item.ctx import CtxItem
    from huey.connectors.pyhuey.plugin.huey_tools.bridge import HueyBridgeResult
    from huey.connectors.pyhuey.plugin.huey_tools.plugin import Plugin

    plugin = Plugin()
    calls = []
    result = HueyBridgeResult(
        command=["python", "script.py"],
        cwd=Path("/workspace"),
        returncode=0,
        stdout='{"ready": true}',
        stderr="",
        parsed_json={"ready": True},
        ok=True,
    )
    bridge = SimpleNamespace(
        status=lambda: {"ready": True},
        check_ffmpeg=lambda **kwargs: calls.append(("ffmpeg", kwargs)) or result,
        prepare_audio=lambda *args, **kwargs: (
            calls.append(("audio", args, kwargs)) or result
        ),
        probe_media=lambda path: calls.append(("probe", path)) or result,
        list_available_scripts=lambda: {
            "check_ffmpeg_environment": True,
            "prepare_audio_for_transcription": False,
            "probe_media": True,
        },
    )
    monkeypatch.setattr(plugin, "_bridge", lambda: bridge)

    ctx = CtxItem()
    output = plugin.cmd(
        ctx,
        [
            {"cmd": "huey_status", "params": {"include_paths": False}},
            {"cmd": "huey_ffmpeg_check", "params": {"strict": True}},
            {"cmd": "huey_prepare_audio", "params": {"source_path": "/tmp/a.wav"}},
            {"cmd": "huey_probe_media", "params": {"path": "/tmp/a.mp4"}},
            {"cmd": "huey_list_tools", "params": {"group": "media"}},
            {
                "cmd": "huey_generate_task_prompt",
                "params": {"task_id": "media_manager"},
            },
            {"cmd": "huey_safety_policy", "params": {"include_blocked_actions": False}},
            "malformed command",
            {"cmd": "not_allowed", "params": {}},
        ],
    )

    assert [item["ok"] for item in output] == [True] * 7 + [False]
    assert output[4]["result"]["group"] == "media"
    assert output[5]["result"]["prompt"]
    assert "blocked_actions" not in output[6]["result"]
    assert '"ready": true' in ctx.extra[plugin.id][0]["display"]
    assert calls == [
        ("ffmpeg", {"strict": True}),
        ("audio", ("/tmp/a.wav",), {"output_path": None, "overwrite": False}),
        ("probe", "/tmp/a.mp4"),
    ]


def test_plugin_validation_errors_safety_and_event_handlers(monkeypatch) -> None:
    from huey.connectors.pyhuey.core.events import Event
    from huey.connectors.pyhuey.plugin.huey_tools.plugin import Plugin

    plugin = Plugin()
    monkeypatch.setattr(
        plugin,
        "_bridge",
        lambda: SimpleNamespace(probe_media=lambda _path: None),
    )
    missing = plugin.execute_command("huey_probe_media", {})
    assert missing["ok"] is False
    assert "required string" in missing["error"]
    wrong_type = plugin.execute_command(
        "huey_prepare_audio", {"source_path": "/tmp/a", "overwrite": True}
    )
    assert wrong_type["ok"] is False
    assert "Overwrite is blocked" in wrong_type["error"]
    assert plugin.execute_command("unknown", {})["error"] == "Unknown command"

    syntax_data = {}
    syntax = plugin.handle(SimpleNamespace(name=Event.CMD_SYNTAX, data=syntax_data))
    assert syntax and syntax_data["commands"] == syntax
    assert plugin.handle(SimpleNamespace(name="unsupported", data={})) is None
    assert plugin.handle(SimpleNamespace(name=Event.CMD_EXECUTE, data={})) == []


def test_plugin_settings_accept_supported_workspace_formats(monkeypatch) -> None:
    from huey.connectors.pyhuey.plugin.huey_tools.plugin import Plugin

    plugin = Plugin()
    plugin.set_option_value("allowed_workspace_roots", "/one:/two")
    settings = plugin._settings()
    assert settings.allowed_workspace_roots == ["/one", "/two"]
    plugin.set_option_value("allowed_workspace_roots", ["/three", ""])
    assert plugin._settings().allowed_workspace_roots == ["/three"]
    plugin.set_option_value("allowed_workspace_roots", 17)
    assert isinstance(plugin._settings().allowed_workspace_roots, list)
