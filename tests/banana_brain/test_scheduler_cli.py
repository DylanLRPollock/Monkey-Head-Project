"""Tests for the Banana Brain command line client's parsing and commands."""

from __future__ import annotations

import argparse
import io
import sys
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

    async def request_ok(self, method, path, body=None):  # noqa: C901,RUF100
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
        "api_socket_path: /run/bb.sock\n"
        "api_bind: 127.0.0.1:12\n"
        "api_token: cfg-token-123456789\n"
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


@pytest.mark.asyncio
async def test_client_unix_socket_context_and_transport_errors(monkeypatch):
    calls = {}

    class Session:
        async def close(self):
            calls["closed"] = True

        def request(self, *args, **kwargs):
            raise aiohttp.ClientError("connection reset")

    monkeypatch.setattr(
        cli.aiohttp,
        "UnixConnector",
        lambda *, path: calls.setdefault("socket", path),
    )
    monkeypatch.setattr(cli.aiohttp, "ClientSession", lambda **kwargs: Session())
    client = cli.Client(socket_path="/tmp/banana.sock")
    assert client.endpoint == "unix:/tmp/banana.sock"
    await client.__aenter__()
    assert calls["socket"] == "/tmp/banana.sock"
    with pytest.raises(cli.APIError, match="transport error"):
        await client.request("GET", "/health")
    await client.__aexit__()
    assert calls["closed"] is True
    assert client._session is None
    await client.__aexit__()  # exiting an already closed context is harmless


@pytest.mark.asyncio
async def test_cli_commands_cover_empty_payloads_and_failure_responses(  # noqa: C901,RUF100
    capsys,
):
    class EmptyClient(FakeClient):
        async def request_ok(self, method, path, body=None):
            self.calls.append((method, path, body))
            if path == "/status":
                return {}
            if path.startswith("/jobs?") or path.endswith("/events?limit=100"):
                return {}
            if path.startswith("/jobs/"):
                return {"id": "bare", "state": "pending"}
            if path == "/queue":
                return {"size": 0}
            if path == "/suspended":
                return {}
            if path == "/mode" and method == "GET":
                return {
                    "mode": "maintenance",
                    "safety_halted": True,
                    "safety_halt_reason": "hot",
                }
            if path == "/watchdog":
                return {"running": False, "signals": []}
            if path == "/adapters":
                return {}
            if path == "/mode" and method == "POST":
                return {
                    "success": False,
                    "from_mode": "ai",
                    "to_mode": "image",
                    "error": "could not switch",
                    "interrupted_job_id": "j",
                }
            if path == "/mode/resume":
                return {"success": False, "to_mode": "ai"}
            return {"success": True}

    client = EmptyClient()
    commands = [
        ["status"],
        ["jobs", "list", "--state", "pending"],
        ["jobs", "show", "bare"],
        ["jobs", "events", "bare"],
        ["queue"],
        ["suspended", "list"],
        ["mode", "get"],
        ["mode", "set", "image"],
        ["mode", "resume"],
        ["adapters"],
        ["watchdog"],
    ]
    results = [await cli._dispatch(args_for(*command), client) for command in commands]
    assert results[7] == cli.ExitCode.APP_ERROR
    assert results[8] == cli.ExitCode.APP_ERROR
    output = capsys.readouterr()
    assert "no jobs" in output.out
    assert "no events" in output.out
    assert "no suspended jobs" in output.out
    assert "no adapters registered" in output.out
    assert "could not switch" in output.out
    assert "still running" in output.err


@pytest.mark.asyncio
async def test_watch_timeout_and_health_http_error(capsys):
    class PendingClient(FakeClient):
        async def request(self, method, path, body=None):
            return 503, {"error": "offline"}

        async def request_ok(self, method, path, body=None):
            return {"id": "pending", "state": "running"}

    client = PendingClient()
    assert await cli._cmd_health(args_for("health"), client) == cli.ExitCode.APP_ERROR
    with pytest.raises(cli.APIError, match="did not finish"):
        await cli._cmd_jobs_watch(
            argparse.Namespace(id="pending", timeout=0, interval=0, json=False),
            client,
        )
    assert "status:            503" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_cli_json_command_paths_and_error_message_shapes(capsys):
    client = FakeClient()
    with pytest.raises(ValueError, match="socket_path or base_url"):
        cli.Client()

    assert cli._extract_error_message({"error": {"message": "nested"}}) == "nested"
    assert cli._extract_error_message({"error": {"message": 7}}).startswith(
        "HTTP error"
    )
    assert cli._extract_error_message({"error": "plain"}) == "plain"
    assert cli._extract_error_message({"raw": "text"}) == "text"
    assert cli._extract_error_message({"other": 1}).startswith("HTTP error")

    assert (
        await cli._cmd_health(argparse.Namespace(json=True), client) == cli.ExitCode.OK
    )
    assert (
        await cli._cmd_status(argparse.Namespace(json=True), client) == cli.ExitCode.OK
    )
    assert (
        await cli._cmd_jobs_cancel(
            argparse.Namespace(id="j", force=False, json=True), client
        )
        == cli.ExitCode.OK
    )
    assert (
        await cli._cmd_queue(argparse.Namespace(limit=None, json=True), client)
        == cli.ExitCode.OK
    )
    assert (
        await cli._cmd_mode_set(
            argparse.Namespace(mode="ai", reason="test", force=False, json=True), client
        )
        == cli.ExitCode.OK
    )
    assert (
        await cli._cmd_mode_resume(argparse.Namespace(reason="test", json=True), client)
        == cli.ExitCode.OK
    )
    assert (
        await cli._cmd_mode_clear_halt(
            argparse.Namespace(reason="test", cleared_by="operator", json=True), client
        )
        == cli.ExitCode.OK
    )
    assert (
        await cli._cmd_pause(argparse.Namespace(reason="test", json=True), client)
        == cli.ExitCode.OK
    )
    assert (
        await cli._cmd_resume(argparse.Namespace(reason="test", json=True), client)
        == cli.ExitCode.OK
    )
    assert await cli._cmd_vram(argparse.Namespace(json=True), client) == cli.ExitCode.OK
    capsys.readouterr()


@pytest.mark.asyncio
async def test_watch_repeated_state_and_optional_queue_limit(capsys):
    class RepeatingClient(FakeClient):
        def __init__(self):
            super().__init__()
            self.states = iter(("running", "running", "completed"))

        async def request_ok(self, method, path, body=None):
            self.calls.append((method, path, body))
            if path == "/jobs/job":
                return {"id": "job", "state": next(self.states)}
            if path == "/queue":
                return {"size": 0, "entries": []}
            return {"success": True}

    client = RepeatingClient()
    args = argparse.Namespace(id="job", timeout=2, interval=0, json=True)
    assert await cli._cmd_jobs_watch(args, client) == cli.ExitCode.OK
    await cli._cmd_queue(argparse.Namespace(limit=10, json=True), client)
    assert client.calls[-1][1] == "/queue?limit=10"
    capsys.readouterr()


@pytest.mark.asyncio
async def test_cli_rich_status_watch_and_mode_branches(  # noqa: C901,RUF100
    tmp_path, monkeypatch, capsys
):
    class RichClient(FakeClient):
        async def request(self, method, path, body=None):
            return 200, {"ok": True}

        async def request_ok(self, method, path, body=None):
            self.calls.append((method, path, body))
            if path == "/status":
                return {
                    "uptime_seconds": 5,
                    "scheduler": {"shutting_down": True, "current_job_id": "j"},
                    "mode": {
                        "mode": "maintenance",
                        "safety_halted": True,
                        "safety_halt_reason": "temperature",
                    },
                    "watchdog": {
                        "signals": [
                            {"severity": "critical", "name": "gpu", "message": "hot"}
                        ]
                    },
                    "adapters": [],
                    "gpu": {
                        "identity": {"name": "V100", "index": 0, "uuid": "GPU-1"},
                        "used_vram_bytes": 1,
                        "total_vram_bytes": 2,
                        "free_vram_bytes": 1,
                        "temperature_c": 88,
                        "power_watts": 250,
                    },
                }
            if path == "/jobs/done":
                return {"id": "done", "state": "failed", "last_error": "oom"}
            if path == "/mode" and method == "GET":
                return {
                    "mode": "maintenance",
                    "safety_halted": True,
                    "safety_halt_reason": "temperature",
                }
            if path == "/watchdog/ack":
                return {"acknowledged": True}
            if path == "/jobs?limit=50":
                return {"jobs": []}
            if path == "/jobs/done/events?limit=100":
                return {"events": []}
            if path == "/queue":
                return {"size": 0, "entries": []}
            if path == "/suspended":
                return {"jobs": []}
            return {
                "success": False,
                "from_mode": "ai",
                "to_mode": "image",
                "error": "blocked",
                "suspended_count": 2,
                "interrupted_job_id": "running",
            }

    client = RichClient()
    assert await cli._dispatch(args_for("status"), client) == cli.ExitCode.OK
    assert (
        await cli._dispatch(args_for("jobs", "watch", "done", "--timeout", "1"), client)
        == cli.ExitCode.OK
    )
    assert (
        await cli._dispatch(args_for("--json", "jobs", "watch", "done"), client)
        == cli.ExitCode.OK
    )
    assert await cli._dispatch(args_for("mode", "get"), client) == cli.ExitCode.OK
    assert (
        await cli._dispatch(args_for("mode", "set", "image"), client)
        == cli.ExitCode.APP_ERROR
    )
    assert (
        await cli._dispatch(args_for("--json", "watchdog", "ack", "gpu"), client)
        == cli.ExitCode.OK
    )
    assert await cli._dispatch(args_for("jobs", "list"), client) == cli.ExitCode.OK
    assert (
        await cli._dispatch(args_for("jobs", "events", "done"), client)
        == cli.ExitCode.OK
    )
    assert await cli._dispatch(args_for("queue"), client) == cli.ExitCode.OK
    assert await cli._dispatch(args_for("suspended", "list"), client) == cli.ExitCode.OK
    output = capsys.readouterr()
    assert "temperature" in output.out
    assert "V100" in output.out
    assert "final state: failed" in output.out
    assert "blocked" in output.out
    assert "still running" in output.err


@pytest.mark.asyncio
async def test_cli_json_submit_priority_and_config_socket_fallback(
    tmp_path, monkeypatch, capsys
):
    class InputClient(FakeClient):
        async def request_ok(self, method, path, body=None):
            self.calls.append((method, path, body))
            if method == "GET" and path == "/jobs/running":
                return {"id": "running", "state": "running"}
            if method == "GET" and path == "/jobs/pending":
                return {"id": "pending", "state": "pending", "adapter": "ollama"}
            if method == "POST" and path == "/jobs":
                return {"id": "replacement", "adapter": "ollama"}
            return {"id": "cancelled", "state": "cancelled"}

    client = InputClient()
    with pytest.raises(cli.APIError, match="running; cancel it first"):
        await cli._dispatch(args_for("jobs", "priority", "running", "40"), client)
    assert (
        await cli._dispatch(
            args_for("--json", "jobs", "priority", "pending", "40"), client
        )
        == cli.ExitCode.OK
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"adapter":"ollama"}'))
    assert (
        await cli._dispatch(args_for("--json", "jobs", "submit", "-"), client)
        == cli.ExitCode.OK
    )
    assert (
        await cli._dispatch(args_for("--json", "suspended", "cancel", "s1"), client)
        == cli.ExitCode.OK
    )

    monkeypatch.setattr(
        cli,
        "_load_config_safe",
        lambda _path: argparse.Namespace(
            api_bind=None, api_socket_path="/run/test.sock", api_token=None
        ),
    )
    sock_client = cli._build_client(
        argparse.Namespace(config="unused", url=None, socket=None, token=None)
    )
    assert sock_client.endpoint == "unix:/run/test.sock"
    assert "replacement" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_priority_plain_output_and_remaining_cli_fallbacks(capsys, monkeypatch):
    class PriorityClient:
        async def request_ok(self, method, path, body=None):
            if method == "GET" and path == "/jobs/old":
                return {
                    "id": "old",
                    "state": "pending",
                    "adapter": "ollama",
                    "payload": {"prompt": "x"},
                }
            if method == "POST" and path == "/jobs":
                return {"id": "new"}
            return {"ok": True}

    args = args_for("jobs", "priority", "old", "90")
    assert await cli._dispatch(args, PriorityClient()) == cli.ExitCode.OK
    out, err = capsys.readouterr()
    assert "replaced old with new at priority 90" in out
    assert "fresh id" in err
    assert cli._fmt_bytes(1024**4 * 1024) == "1024.0 TiB"

    original_import = __import__

    def fail_config_import(name, *args, **kwargs):
        if name == "huey.banana_brain.config":
            raise ImportError("optional config unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fail_config_import)
    assert cli._load_config_safe("ignored.yaml") is None
    monkeypatch.undo()

    from huey.banana_brain.config import ConfigError

    def fail_config_load(_path):
        raise ConfigError("invalid settings")

    monkeypatch.setattr("huey.banana_brain.config.load_config", fail_config_load)
    assert cli._load_config_safe("bad.yaml") is None
