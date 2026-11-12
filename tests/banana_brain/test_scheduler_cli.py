"""Tests for the Banana Brain command line client's parsing and commands."""

from __future__ import annotations

import argparse
from typing import ClassVar

import aiohttp
import pytest

from huey.banana_brain import scheduler_cli as cli


class FakeClient:
    endpoint = "http://localhost"

    def __init__(self):
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def request(self, method, path, body=None):
        self.calls.append((method, path, body))
        if path == "/health":
            return 200, {"ok": True, "mode": "ai"}
        return 200, {"ok": True}

    async def request_ok(self, method, path, body=None):
        self.calls.append((method, path, body))
        if path == "/status":
            return {
                "uptime_seconds": 65,
                "scheduler": {"pending_jobs": 2},
                "mode": {"mode": "ai"},
                "watchdog": {"signals": []},
                "adapters": ["ollama"],
                "gpu": {},
            }
        if path == "/jobs?limit=50":
            return {
                "jobs": [
                    {
                        "id": "123456789",
                        "adapter": "ollama",
                        "state": "pending",
                        "priority": 80,
                        "submitted_at": 1,
                    }
                ]
            }
        if path.startswith("/jobs/") and path.endswith("/events?limit=100"):
            return {
                "events": [
                    {
                        "at": 1,
                        "kind": "transition",
                        "from_state": "pending",
                        "to_state": "running",
                    }
                ]
            }
        if path == "/jobs/old":
            return {
                "id": "old",
                "adapter": "ollama",
                "payload": {"prompt": "x"},
                "state": "pending",
                "priority": 20,
                "exclusive": False,
                "submitted_at": 10,
                "started_at": None,
                "finished_at": None,
                "attempts": 0,
                "max_attempts": 2,
                "estimated_vram_bytes": 1,
                "deadline": 20,
                "idempotency_key": "once",
                "last_error": "oops",
                "result": {"text": "ok"},
                "tags": {},
            }
        if path.startswith("/jobs/"):
            return {"id": "job", "state": "completed", "adapter": "ollama"}
        if path == "/queue":
            return {
                "size": 1,
                "entries": [
                    {
                        "id": "123456789",
                        "adapter": "ollama",
                        "state": "pending",
                        "base_priority": 20,
                        "effective_priority": 30,
                        "aging_bonus": 10,
                        "overdue": True,
                        "age_seconds": 70,
                    }
                ],
            }
        if path == "/suspended":
            return {
                "jobs": [
                    {"id": "s1", "adapter": "audio", "priority": 40, "age_seconds": 3}
                ]
            }
        if path == "/mode" and method == "GET":
            return {
                "mode": "ai",
                "mode_since": 1,
                "mode_age_seconds": 2,
                "mode_reason": "test",
                "mode_requested_by": "cli",
                "safety_halted": False,
                "previous_non_exclusive_mode": "ai",
                "suspended_jobs": 0,
                "current_job_id": "123456789",
            }
        if path == "/mode/resume":
            return {"success": True, "to_mode": "ai", "elapsed_s": 2}
        if path == "/mode/clear-halt":
            return {"safety_halted": False}
        if path == "/watchdog":
            return {
                "running": True,
                "run_count": 2,
                "last_run_at": 1,
                "check_interval_s": 5,
                "signals": [
                    {
                        "severity": "warn",
                        "name": "hot",
                        "message": "warm",
                        "key": "temp",
                    }
                ],
                "cancel_requested": 1,
                "service_failures": 2,
            }
        if path == "/vram":
            return {
                "gpu_state_known": True,
                "total_vram_bytes": 100,
                "free_vram_bytes": 80,
                "committed_bytes": 10,
                "headroom_bytes": 5,
                "allocatable_bytes": 75,
                "reservation_count": 1,
                "reservations": [
                    {
                        "job_id": "j",
                        "adapter": "ollama",
                        "bytes": 10,
                        "state": "running",
                        "age_seconds": 4,
                    }
                ],
                "last_refusal": "none",
            }
        if path == "/adapters":
            return {"adapters": ["ollama", "audio"]}
        if path.startswith("POST:"):
            return {
                "id": "new",
                "adapter": "ollama",
                "state": "pending",
                "success": True,
                "from_mode": "ai",
                "to_mode": "image",
                "elapsed_s": 1,
                "suspended_count": 0,
            }
        return {
            "id": "new",
            "adapter": "ollama",
            "state": "pending",
            "success": True,
            "from_mode": "ai",
            "to_mode": "image",
            "elapsed_s": 1,
            "suspended_count": 0,
        }


def args_for(*parts):
    return cli._build_parser().parse_args(list(parts))


def test_formatting_parsing_and_config_precedence(tmp_path, monkeypatch):
    assert cli._fmt_duration(None) == "-"
    assert cli._fmt_duration("bad") == "-"
    assert cli._fmt_duration(-1) == "0s"
    assert cli._fmt_duration(61) == "1m01s"
    assert cli._fmt_duration(3600) == "1h00m"
    assert cli._fmt_duration(86400) == "1d00h"
    assert cli._fmt_bytes(None) == "-"
    assert cli._fmt_bytes("bad") == "-"
    assert cli._fmt_bytes(10) == "10 B"
    assert cli._fmt_bytes(1024) == "1.0 KiB"
    assert cli._fmt_bytes(1024**4) == "1.0 TiB"
    assert cli._fmt_ts(None) == "-"
    assert cli._fmt_ts("bad") == "-"
    assert cli._short_id(None) == "-"
    assert cli._short_id("123456789") == "12345678"
    assert cli._now_minus(None) is None
    assert cli._extract_error_message({"error": {"message": "bad"}}) == "bad"
    assert cli._extract_error_message({"error": "no"}) == "no"
    assert cli._extract_error_message({"raw": "x" * 500}) == "x" * 400
    assert cli._extract_error_message(None) == "unknown error"
    assert "response body" in cli._extract_error_message({"unexpected": 1})
    assert cli._parse_priority_arg(" interactive ") == 80
    assert cli._parse_priority_arg("100") == 100
    for value in ("oops", "101", "-1"):
        with pytest.raises(cli.APIError):
            cli._parse_priority_arg(value)

    cfg = tmp_path / "bb.yaml"
    cfg.write_text(
        "api_socket_path: /run/bb.sock\napi_bind: 127.0.0.1:12\napi_token: cfg-token-123456789\n"
    )
    monkeypatch.delenv("BANANA_BRAIN_TOKEN", raising=False)
    default = cli._build_client(
        argparse.Namespace(config=str(cfg), url=None, socket=None, token=None)
    )
    assert default.endpoint == "http://127.0.0.1:12"
    assert default._token == "cfg-token-123456789"
    explicit = cli._build_client(
        argparse.Namespace(config="missing", url=None, socket="/tmp/sock", token="flag")
    )
    assert explicit.endpoint == "unix:/tmp/sock"
    monkeypatch.setenv("BANANA_BRAIN_TOKEN", "env")
    explicit_url = cli._build_client(
        argparse.Namespace(
            config="missing", url="http://host", socket="/tmp/sock", token=None
        )
    )
    assert explicit_url.endpoint == "http://host"
    assert explicit_url._token == "env"
    assert cli._resolve_config_path(None) is None


class Response:
    def __init__(self, status, text):
        self.status, self._text = status, text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def text(self):
        return self._text


@pytest.mark.asyncio
async def test_client_request_errors_and_context(monkeypatch):
    client = cli.Client(base_url="http://localhost", token="t")
    with pytest.raises(RuntimeError):
        await client.request("GET", "/")

    class Session:
        _default_headers: ClassVar[dict[str, str]] = {"Authorization": "Bearer t"}

        async def close(self):
            pass

        def request(self, *args, **kwargs):
            return Response(200, "")

    monkeypatch.setattr(cli.aiohttp, "ClientSession", lambda **kwargs: Session())
    await client.__aenter__()
    assert client._session._default_headers["Authorization"] == "Bearer t"
    assert await client.request("GET", "/") == (200, None)
    client._session.request = lambda *args, **kwargs: Response(200, "not-json")
    assert await client.request("GET", "/") == (200, {"raw": "not-json"})
    client._session.request = lambda *args, **kwargs: Response(200, '{"ok":true}')
    assert await client.request_ok("GET", "/") == {"ok": True}
    client._session.request = lambda *args, **kwargs: Response(
        403, '{"error":"denied"}'
    )
    with pytest.raises(cli.APIError, match="denied"):
        await client.request_ok("GET", "/")
    client._session = None


@pytest.mark.asyncio
async def test_dispatches_all_command_families_and_text_output(
    tmp_path, capsys, monkeypatch
):
    client = FakeClient()
    commands = [
        ["health"],
        ["status"],
        ["jobs", "list"],
        ["jobs", "show", "old"],
        ["jobs", "cancel", "job", "--force"],
        ["jobs", "watch", "job"],
        ["jobs", "events", "job"],
        ["queue"],
        ["suspended", "list"],
        ["suspended", "cancel", "s1"],
        ["mode"],
        ["mode", "set", "image"],
        ["mode", "resume"],
        ["mode", "clear-halt", "--reason", "done"],
        ["pause"],
        ["resume"],
        ["vram"],
        ["watchdog"],
        ["watchdog", "ack", "temp"],
        ["adapters"],
    ]
    for command in commands:
        result = await cli._dispatch(args_for(*command), client)
        assert result == cli.ExitCode.OK
    output = capsys.readouterr()
    assert "watchdog" in output.out
    assert "note:" in output.err

    submission = tmp_path / "job.json"
    submission.write_text('{"adapter":"ollama","payload":{}}')
    args = args_for("jobs", "submit", str(submission))
    assert await cli._dispatch(args, client) == cli.ExitCode.OK
    assert any(
        call == ("POST", "/jobs", {"adapter": "ollama", "payload": {}})
        for call in client.calls
    )


@pytest.mark.asyncio
async def test_command_edge_cases_json_empty_watch_timeout_and_priority(
    tmp_path, capsys, monkeypatch
):
    client = FakeClient()
    for command in [
        ["--json", "jobs", "list"],
        ["--json", "jobs", "show", "old"],
        ["--json", "jobs", "events", "job"],
        ["--json", "queue"],
        ["--json", "suspended", "list"],
        ["--json", "mode", "get"],
        ["--json", "vram"],
        ["--json", "watchdog"],
        ["--json", "adapters"],
    ]:
        assert await cli._dispatch(args_for(*command), client) == cli.ExitCode.OK
    args = args_for("--json", "jobs", "priority", "old", "BATCH")
    assert await cli._dispatch(args, client) == cli.ExitCode.OK
    assert any(call[0:2] == ("POST", "/jobs/old/cancel") for call in client.calls)

    with pytest.raises(cli.APIError, match="file not found"):
        await cli._dispatch(
            args_for("jobs", "submit", str(tmp_path / "missing")), client
        )
    invalid = tmp_path / "invalid.json"
    invalid.write_text("[]")
    with pytest.raises(cli.APIError, match="JSON object"):
        await cli._dispatch(args_for("jobs", "submit", str(invalid)), client)
    invalid.write_text("bad")
    with pytest.raises(cli.APIError, match="invalid JSON"):
        await cli._dispatch(args_for("jobs", "submit", str(invalid)), client)
    with pytest.raises(cli.APIError, match="already completed"):
        await cli._dispatch(args_for("jobs", "priority", "job", "40"), client)
    with pytest.raises(cli.APIError, match="unknown watchdog"):
        await cli._cmd_watchdog(
            argparse.Namespace(watchdog_command="bad", json=False), client
        )
    with pytest.raises(cli.APIError, match="no handler"):
        await cli._dispatch(argparse.Namespace(command="unknown"), client)


def test_main_exit_codes_and_argument_errors(monkeypatch, capsys):
    async def app_error(_args):
        raise cli.APIError(404, "missing")

    monkeypatch.setattr(cli, "_async_main", app_error)
    assert cli.main(["health"]) == cli.ExitCode.APP_ERROR
    assert "missing" in capsys.readouterr().err

    async def keyboard(_args):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "_async_main", keyboard)
    assert cli.main(["health"]) == cli.ExitCode.APP_ERROR

    async def unexpected(_args):
        raise RuntimeError("oops")

    monkeypatch.setattr(cli, "_async_main", unexpected)
    assert cli.main(["health"]) == cli.ExitCode.APP_ERROR
    with pytest.raises(SystemExit) as exc:
        cli.main(["jobs", "list", "--limit", "bad"])
    assert exc.value.code == 2


@pytest.mark.asyncio
async def test_async_main_handles_connector_errors(monkeypatch, capsys):
    client = FakeClient()

    async def fail(_args, _client):
        key = argparse.Namespace(host="localhost", port=80, ssl=False)
        raise aiohttp.ClientConnectorError(key, OSError("offline"))

    monkeypatch.setattr(cli, "_build_client", lambda _args: client)
    monkeypatch.setattr(cli, "_dispatch", fail)
    assert await cli._async_main(args_for("health")) == cli.ExitCode.TRANSPORT
    assert "cannot reach Banana Brain API" in capsys.readouterr().err
