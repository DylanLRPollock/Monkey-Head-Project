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
        "huey_connections",
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
    assert len(responses[2]["result"]["tools"]) == 5


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


def test_default_health_port_matches_huey_api(monkeypatch):
    monkeypatch.delenv("HUEY_API_PORT", raising=False)
    config = pygpt_cli.connector_config()["mcpServers"]["hueyos"]
    assert config["env"]["HUEY_API_PORT"] == "1995"
    assert pygpt_cli.doctor()["huey_api_port"] == "1995"


def test_gui_executes_upstream_binary_not_stub(monkeypatch, tmp_path):
    called = {}
    monkeypatch.setattr(pygpt_cli, "pygpt_executable", lambda: "/usr/bin/pygpt")

    def fake_run(command, **kwargs):
        called["command"] = command
        called["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(pygpt_cli.subprocess, "run", fake_run)
    assert pygpt_cli.launch_gui(workdir=tmp_path) == 0
    assert called["command"] == ["/usr/bin/pygpt"]
    assert called["kwargs"]["env"]["PYGPT_WORKDIR"] == str(Path(tmp_path).resolve())
    assert called["kwargs"]["check"] is False
    assert called["kwargs"]["shell"] is False


def test_missing_upstream_gui_fails_clearly(monkeypatch, capsys):
    monkeypatch.setattr(pygpt_cli, "pygpt_executable", lambda: None)
    assert pygpt_cli.main(["gui"]) == 2
    assert "PyGPT executable not found" in capsys.readouterr().err


def test_mcp_permission_policy_does_not_claim_to_sandbox_upstream():
    policy = pygpt_mcp.permissions()
    assert policy["mode"] == "read-only"
    assert "hardware_actuation" in policy["not_exposed"]
    assert "other PyGPT plugins" in policy["note"]


def test_tool_failure_is_logged_locally_without_leaking_details(monkeypatch, caplog):
    def broken():
        raise RuntimeError("local diagnostic detail")

    monkeypatch.setitem(pygpt_mcp._ACTIONS, "huey_health", broken)
    response = pygpt_mcp.dispatch(request("tools/call", {"name": "huey_health"}))
    assert response["result"]["isError"] is True
    assert "local diagnostic detail" not in str(response)
    assert "local diagnostic detail" in caplog.text


def test_failed_health_is_an_mcp_tool_error(monkeypatch):
    monkeypatch.setenv("HUEY_API_PORT", "0")
    response = pygpt_mcp.dispatch(request("tools/call", {"name": "huey_health"}))
    assert response["result"]["isError"] is True
    assert "Invalid HUEY_API_PORT" in response["result"]["content"][0]["text"]


def test_connections_summarizes_status(monkeypatch):
    monkeypatch.setattr(pygpt_mcp, "health_info", lambda: {"connected": True})
    monkeypatch.setattr(
        pygpt_mcp,
        "diagnostics",
        lambda: {"ffmpeg_available": True, "ffprobe_available": True},
    )
    result = pygpt_mcp.connections()
    assert result["all_connected"] is True
    assert result["mcp"]["mode"] == "read-only"


def test_project_info_handles_uninstalled_distribution(monkeypatch):
    monkeypatch.setattr(
        pygpt_mcp.importlib.metadata,
        "version",
        lambda _name: (_ for _ in ()).throw(pygpt_mcp.importlib.metadata.PackageNotFoundError),
    )
    assert pygpt_mcp.project_info()["package_version"] is None


@pytest.mark.parametrize(
    ("port", "response", "expected"),
    [
        ("abc", None, {"connected": False, "error": "Invalid HUEY_API_PORT"}),
        ("0", None, {"connected": False, "error": "Invalid HUEY_API_PORT"}),
        ("8080", (503, b"{}"), {"connected": False, "status_code": 503}),
        ("8080", (200, b"[]"), {"connected": False, "error": "Unexpected API response"}),
        ("8080", (200, b"not json"), {"connected": False, "error": "JSONDecodeError"}),
        ("8080", OSError("offline"), {"connected": False, "error": "OSError"}),
    ],
)
def test_health_failure_paths_close_loopback_connection(monkeypatch, port, response, expected):
    closed = []

    class FakeHTTP:
        def __init__(self, host, port, timeout):
            assert host == "127.0.0.1"
            assert timeout == 2

        def request(self, method, path):
            assert method == "GET" and path == "/healthz"

        def getresponse(self):
            if isinstance(response, Exception):
                raise response
            status, payload = response
            return SimpleNamespace(status=status, read=lambda limit: payload)

        def close(self):
            closed.append(True)

    monkeypatch.setenv("HUEY_API_PORT", port)
    monkeypatch.setattr(pygpt_mcp.http.client, "HTTPConnection", FakeHTTP)
    assert pygpt_mcp.health_info() == expected
    assert closed == ([] if port in {"abc", "0"} else [True])


def test_mcp_protocol_and_json_rpc_invalid_shapes():
    initialized = pygpt_mcp.dispatch(request("initialize", {"protocolVersion": "future"}))
    assert initialized["result"]["protocolVersion"] == "2025-06-18"

    assert pygpt_mcp.dispatch([])["error"]["code"] == -32600
    assert pygpt_mcp.dispatch({"jsonrpc": "1.0", "id": 1, "method": "ping"})["error"]["code"] == -32600
    for request_id in (True, [], {}):
        response = pygpt_mcp.dispatch({"jsonrpc": "2.0", "id": request_id, "method": "ping"})
        assert response["error"]["code"] == -32600
    assert pygpt_mcp.dispatch({"jsonrpc": "2.0", "id": 4, "method": None})["error"]["code"] == -32600
    assert pygpt_mcp.dispatch(request("ping", []))["error"]["code"] == -32602
    assert pygpt_mcp.dispatch(request("not-a-method"))["error"]["code"] == -32601


def test_mcp_rejects_non_object_tool_arguments_and_reports_disconnected(monkeypatch):
    response = pygpt_mcp.dispatch(request("tools/call", {"name": "huey_project", "arguments": ["unexpected"]}))
    assert response["error"]["message"] == "Tool takes no arguments"

    monkeypatch.setattr(pygpt_mcp, "health_info", lambda: {"connected": False, "error": "offline"})
    monkeypatch.setattr(pygpt_mcp, "diagnostics", lambda: {"ffmpeg_available": False, "ffprobe_available": True})
    result = pygpt_mcp.connections()
    assert result["all_connected"] is False
    assert result["media_tools"]["ffmpeg_available"] is False


def test_mcp_stdio_skips_notification_responses_and_main_returns_zero(monkeypatch):
    source = io.StringIO(
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
    )
    target = io.StringIO()
    pygpt_mcp.serve(source, target)
    assert target.getvalue() == ""
    monkeypatch.setattr(pygpt_mcp, "serve", lambda: None)
    assert pygpt_mcp.main() == 0
