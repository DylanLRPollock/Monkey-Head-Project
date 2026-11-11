"""Cover PyGPT executable discovery and CLI dispatch branches."""

from __future__ import annotations

import json
from types import SimpleNamespace

from huey.integrations import pygpt_cli


def test_executable_resolution_honors_override_and_path(monkeypatch):
    resolved = []
    monkeypatch.setattr(
        pygpt_cli.shutil, "which", lambda name: resolved.append(name) or name
    )

    monkeypatch.setenv("PYGPT_EXECUTABLE", "/opt/pygpt")
    assert pygpt_cli.pygpt_executable() == "/opt/pygpt"
    monkeypatch.delenv("PYGPT_EXECUTABLE")
    assert pygpt_cli.pygpt_executable() == "pygpt"
    assert resolved == ["/opt/pygpt", "pygpt"]


def test_doctor_reports_installed_package_and_gui(monkeypatch):
    monkeypatch.setattr(pygpt_cli, "pygpt_executable", lambda: "/usr/bin/pygpt")
    monkeypatch.setattr(
        pygpt_cli.importlib.metadata,
        "version",
        lambda name: "2.9.1" if name == "pygpt-net" else None,
    )

    result = pygpt_cli.doctor()

    assert result["upstream_executable"] == "/usr/bin/pygpt"
    assert result["pygpt_in_current_environment"] == "2.9.1"
    assert result["gui_available"] is True


def test_gui_launch_without_workdir_and_handles_os_error(monkeypatch, capsys):
    monkeypatch.setattr(pygpt_cli, "pygpt_executable", lambda: "/usr/bin/pygpt")
    called = {}

    def run(command, **kwargs):
        called["command"] = command
        called["kwargs"] = kwargs
        raise OSError("cannot execute")

    monkeypatch.setattr(pygpt_cli.subprocess, "run", run)
    assert pygpt_cli.launch_gui() == 2
    assert called["command"] == ["/usr/bin/pygpt"]
    assert "PYGPT_WORKDIR" not in called["kwargs"]["env"]
    assert "Unable to start PyGPT: cannot execute" in capsys.readouterr().err


def test_main_dispatches_mcp_connector_and_doctor(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(pygpt_cli, "serve", lambda: calls.append("serve"))
    assert pygpt_cli.main(["mcp"]) == 0
    assert calls == ["serve"]

    assert pygpt_cli.main(["connector"]) == 0
    connector = json.loads(capsys.readouterr().out)
    assert connector["mcpServers"]["hueyos"]["args"] == [
        "-m",
        "huey.integrations.pygpt_mcp",
    ]

    monkeypatch.setattr(pygpt_cli, "doctor", lambda: {"gui_available": False})
    assert pygpt_cli.main(["doctor"]) == 0
    assert json.loads(capsys.readouterr().out) == {"gui_available": False}


def test_gui_subcommand_forwards_workdir(monkeypatch, tmp_path):
    captured = []
    monkeypatch.setattr(
        pygpt_cli,
        "launch_gui",
        lambda *, workdir=None: captured.append(workdir) or 0,
    )
    assert pygpt_cli.main(["gui", "--workdir", str(tmp_path)]) == 0
    assert captured == [tmp_path]


def test_main_reports_unrecognized_dispatch_state(monkeypatch):
    errors = []
    monkeypatch.setattr(
        pygpt_cli.argparse.ArgumentParser,
        "parse_args",
        lambda _self, _argv: SimpleNamespace(command="unexpected"),
    )
    monkeypatch.setattr(
        pygpt_cli.argparse.ArgumentParser,
        "error",
        lambda _self, message: errors.append(message),
    )

    assert pygpt_cli.main([]) == 2
    assert errors == ["Unsupported command"]
