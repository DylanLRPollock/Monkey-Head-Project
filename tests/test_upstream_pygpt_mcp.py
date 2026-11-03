"""Contract and safety tests for the upstream PyGPT/HueyOS integration."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from huey.integrations import pygpt_cli, pygpt_mcp


def request(method: str, params: dict | None = None) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params if params is not None else {},
    }


def test_mcp_initialize_negotiates_supported_protocol():
    response = pygpt_mcp.dispatch(
        request("initialize", {"protocolVersion": "2024-11-05"})
    )
    assert response["result"]["protocolVersion"] == "2024-11-05"
    assert response["result"]["capabilities"]["tools"] == {"listChanged": False}


def test_mcp_tools_are_explicit_and_read_only():
    response = pygpt_mcp.dispatch(request("tools/list"))
    names = {tool["name"] for tool in response["result"]["tools"]}
    assert names == {
        "huey_project",
        "huey_health",
        "huey_diagnostics",
        "huey_permissions",
    }
    assert "shell_exec" not in names
    assert "hardware_control" not in names


def test_mcp_calls_report_project_information():
    response = pygpt_mcp.dispatch(
        request("tools/call", {"name": "huey_project", "arguments": {}})
    )
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["runtime"] == "HueyOS"
    assert payload["bridge"] == "mcp-stdio-read-only"


@pytest.mark.parametrize(
    "name",
    ["shell_exec", "hardware_control", "governance_mutation", "__import__"],
)
def test_mcp_unknown_tools_are_denied(name):
    response = pygpt_mcp.dispatch(
        request("tools/call", {"name": name, "arguments": {}})
    )
    assert response["error"]["code"] == -32602


def test_mcp_rejects_unexpected_arguments():
    response = pygpt_mcp.dispatch(
        request(
            "tools/call",
            {"name": "huey_project", "arguments": {"command": "rm -rf /"}},
        )
    )
    assert response["error"]["code"] == -32602


def test_mcp_notifications_do_not_emit_responses():
    assert (
        pygpt_mcp.dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"})
        is None
    )


def test_mcp_stdio_processes_valid_and_invalid_json():
    source = io.StringIO(
        "not json\n"
        + json.dumps(request("ping"))
        + "\n"
        + json.dumps(request("tools/list"))
        + "\n"
    )
    target = io.StringIO()
    pygpt_mcp.serve(source, target)
    responses = [json.loads(line) for line in target.getvalue().splitlines()]
    assert responses[0]["error"]["code"] == -32700
    assert responses[1]["result"] == {}
    assert len(responses[2]["result"]["tools"]) == 4


def test_health_refuses_invalid_port_without_network(monkeypatch):
    monkeypatch.setenv("HUEY_API_PORT", "999999")
    assert pygpt_mcp.health_info() == {
        "connected": False,
        "error": "Invalid HUEY_API_PORT",
    }


def test_health_queries_only_loopback(monkeypatch):
    captured = {}

    class FakeHTTP:
        def __init__(self, host, port, timeout):
            captured.update(host=host, port=port, timeout=timeout)

        def request(self, method, path):
            captured.update(method=method, path=path)

        def getresponse(self):
            return SimpleNamespace(
                status=200,
                read=lambda limit: b'{"status":"ok","service":"hueyos"}',
            )

        def close(self):
            captured["closed"] = True

    monkeypatch.setenv("HUEY_API_PORT", "8000")
    monkeypatch.setattr(pygpt_mcp.http.client, "HTTPConnection", FakeHTTP)
    assert pygpt_mcp.health_info()["connected"] is True
    assert captured == {
        "host": "127.0.0.1",
        "port": 8000,
        "timeout": 2,
        "method": "GET",
        "path": "/healthz",
        "closed": True,
    }


def test_connector_export_uses_running_python():
    config = pygpt_cli.connector_config()["mcpServers"]["hueyos"]
    assert config["command"] == sys.executable
    assert config["args"] == ["-m", "huey.integrations.pygpt_mcp"]


def test_gui_executes_upstream_binary_not_stub(monkeypatch, tmp_path):
    called = {}
    monkeypatch.setattr(pygpt_cli, "pygpt_executable", lambda: "/usr/bin/pygpt")

    def fake_run(command, **kwargs):
        called["command"] = command
        called["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(pygpt_cli.subprocess, "run", fake_run)
    assert pygpt_cli.launch_gui(workdir=tmp_path) == 0
    assert called["command"] == [
        "/usr/bin/pygpt",
        f"--workdir={Path(tmp_path).resolve()}",
    ]
    assert called["kwargs"] == {"check": False, "shell": False}


def test_missing_upstream_gui_fails_clearly(monkeypatch, capsys):
    monkeypatch.setattr(pygpt_cli, "pygpt_executable", lambda: None)
    assert pygpt_cli.main(["gui"]) == 2
    assert "PyGPT executable not found" in capsys.readouterr().err


def test_mcp_permission_policy_does_not_claim_to_sandbox_upstream():
    policy = pygpt_mcp.permissions()
    assert policy["mode"] == "read-only"
    assert "hardware_actuation" in policy["not_exposed"]
    assert "other PyGPT plugins" in policy["note"]
