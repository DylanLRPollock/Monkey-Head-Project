from __future__ import annotations

import importlib

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
