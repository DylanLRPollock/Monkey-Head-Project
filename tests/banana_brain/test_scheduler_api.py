"""Route and parsing tests for the local Banana Brain HTTP API."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import ClassVar

import pytest
from aiohttp.test_utils import TestClient, TestServer

from huey.banana_brain import scheduler_api as api_module
from huey.banana_brain.job_models import Job, JobState, Priority
from huey.banana_brain.scheduler import (
    JobNotCancellable,
    SchedulerError,
    SchedulerShuttingDown,
)
from huey.banana_brain.scheduler_api import APIError, SchedulerAPI


class Scheduler:
    is_shutting_down = False
    _adapters: ClassVar[dict[str, object]] = {"ollama": object(), "audio": object()}

    async def status(self):
        return {"pending_jobs": 1}

    async def submit(self, job):
        return job

    async def cancel(self, job_id, *, force=False):
        return True


class Store:
    async def list_recent(self, **kwargs):
        return []

    async def find_by_idempotency_key(self, *args):
        return None

    async def get(self, _job_id):
        return None

    async def list_events(self, *_args, **_kwargs):
        return []


class PriorityQueue:
    async def snapshot(self, *, limit=None):
        return {"limit": limit, "jobs": []}


class Snapshot:
    async def snapshot(self):
        return {"used": 1}


class Modes:
    async def get_state(self):
        return {"mode": "ai", "safety_halted": False}

    async def get_suspended(self):
        return []

    async def cancel_suspended(self, _job_id):
        return False


class Monitor:
    async def get_status(self):
        return None


def make_api(*, token=None, modes=None, watchdog=None, scheduler=None, store=None):
    config = {
        "api_bind": "127.0.0.1:8080",
        "api_token": token,
        "shutdown_grace_seconds": 0.1,
    }
    return SchedulerAPI(
        config,
        scheduler=scheduler or Scheduler(),
        job_store=store or Store(),
        priority_manager=PriorityQueue(),
        vram_manager=Snapshot(),
        gpu_monitor=Monitor(),
        gpu_modes=modes,
        watchdog=watchdog,
    )


@pytest.mark.asyncio
async def test_api_helpers_parse_and_validate_inputs():
    assert api_module._error_kind(400) == "invalid_request_error"
    assert api_module._error_kind(401) == "authentication_error"
    assert api_module._error_kind(403) == "permission_error"
    assert api_module._error_kind(404) == "not_found_error"
    assert api_module._error_kind(409) == "conflict"
    assert api_module._error_kind(422) == "unprocessable_entity"
    assert api_module._error_kind(429) == "rate_limit_error"
    assert api_module._error_kind(503) == "service_unavailable"
    assert api_module._error_kind(599) == "internal_error"
    assert api_module._error_kind(418) == "api_error"

    assert api_module._parse_limit(None, 5) == 5
    assert api_module._parse_limit("", None) is None
    assert api_module._parse_limit("1200", None) == 1000
    assert api_module._parse_limit("0", 5) == 0
    with pytest.raises(APIError):
        api_module._parse_limit("x", 5)
    with pytest.raises(APIError):
        api_module._parse_limit("-1", 5)
    assert api_module._parse_states(None) is None
    assert api_module._parse_states(" , ") is None
    assert api_module._parse_states("pending, completed") == {
        JobState.PENDING,
        JobState.COMPLETED,
    }
    assert api_module._cfg_get(SimpleNamespace(value=1), "value") == 1
    numeric_job = api_module._job_from_body(
        {"adapter": "ollama", "payload": {}, "priority": 40.5}
    )
    assert numeric_job.priority == 40
    assert api_module._job_from_body(
        {"adapter": "ollama", "payload": {}, "priority": None}
    ).priority == int(Priority.BACKGROUND)
    with pytest.raises(ValueError, match="priority must be an int"):
        api_module._job_from_body(
            {"adapter": "ollama", "payload": {}, "priority": True}
        )
    with pytest.raises(APIError):
        api_module._parse_states("missing")

    body = {
        "adapter": "ollama",
        "payload": {"prompt": "hi"},
        "priority": "INTERACTIVE",
        "deadline": "123.5",
        "estimated_vram_bytes": 10,
        "tags": {1: 2},
        "owner": "tester",
        "idempotency_key": "once",
        "max_attempts": 2,
    }
    parsed = api_module._job_from_body(body)
    assert parsed.priority == int(Priority.INTERACTIVE)
    assert parsed.deadline == 123.5
    assert parsed.tags == {"1": "2"}
    assert parsed.max_attempts == 2
    assert api_module._job_from_body(
        {"adapter": "ollama", "payload": {}}
    ).priority == int(Priority.BACKGROUND)
    for bad in [
        {"id": "x", "adapter": "a", "payload": {}},
        {"adapter": "", "payload": {}},
        {"adapter": "a", "payload": []},
        {"adapter": "a", "payload": {}, "priority": True},
        {"adapter": "a", "payload": {}, "priority": "unknown"},
        {"adapter": "a", "payload": {}, "deadline": "bad"},
        {"adapter": "a", "payload": {}, "estimated_vram_bytes": True},
        {"adapter": "a", "payload": {}, "tags": ["not-a-map"]},
        {"adapter": "a", "payload": {}, "owner": 2},
        {"adapter": "a", "payload": {}, "idempotency_key": 3},
        {"adapter": "a", "payload": {}, "max_attempts": True},
    ]:
        with pytest.raises(ValueError):
            api_module._job_from_body(bad)

    class Request:
        def __init__(self, text):
            self._text = text

        async def text(self):
            return self._text

    assert await api_module._read_json(Request(""), optional=True) == {}
    for text in ["", "not json", "[]"]:
        with pytest.raises(APIError):
            await api_module._read_json(Request(text))
    with pytest.raises(APIError):
        await api_module._read_json(Request("[]"), optional=True)
    assert (
        api_module._extract_token(
            SimpleNamespace(headers={"Authorization": "Bearer abc"})
        )
        == "abc"
    )
    assert (
        api_module._extract_token(
            SimpleNamespace(headers={"Authorization": "bearer  "})
        )
        is None
    )
    assert (
        api_module._extract_token(SimpleNamespace(headers={"X-API-Key": " key "}))
        == "key"
    )
    assert api_module._extract_token(SimpleNamespace(headers={})) is None
    assert api_module._severity_rank("CRITICAL") == 3
    assert api_module._severity_rank("other") == 0


@pytest.mark.asyncio
async def test_api_helper_safe_calls_and_gpu_serialization():
    assert await api_module._safe_call(SimpleNamespace(value=1), "missing") is None
    assert await api_module._safe_call(SimpleNamespace(value=1), "value") is None

    class Service:
        async def ok(self):
            return "yes"

        def sync(self):
            return 3

        def broken(self):
            raise RuntimeError("broken")

    service = Service()
    assert await api_module._safe_call(service, "ok") == "yes"
    assert await api_module._safe_call(service, "sync") == 3
    assert await api_module._safe_call(service, "broken") == {"error": "call failed"}
    assert api_module._serialise_gpu_status(None) is None
    assert (
        api_module._serialise_gpu_status(SimpleNamespace(timestamp=1))["identity"]
        is None
    )
    bad = SimpleNamespace(identity=object(), processes=object())
    assert api_module._serialise_gpu_status(bad) is None


@pytest.mark.asyncio
async def test_http_auth_health_routes_and_request_ids():
    api = make_api(token="secret", modes=Modes())
    app = api_module.web.Application(
        middlewares=[
            api._error_middleware,
            api._auth_middleware,
            api._inflight_middleware,
        ]
    )
    api._install_routes(app)
    async with TestClient(TestServer(app)) as client:
        missing = await client.get("/status")
        assert missing.status == 401
        assert missing.headers["WWW-Authenticate"] == "Bearer"
        assert (await missing.json())["error"]["type"] == "authentication_error"
        assert (await client.get("/health")).status == 200
        assert (
            await client.get("/status", headers={"Authorization": "Bearer wrong"})
        ).status == 401
        headers = {"X-API-Key": "secret", "X-Request-Id": "req-123"}
        response = await client.get("/status", headers=headers)
        assert response.status == 200
        assert response.headers["X-Request-Id"] == "req-123"
        assert (await response.json())["adapters"] == ["audio", "ollama"]
        assert (await client.get("/adapters", headers=headers)).status == 200
        assert (await client.get("/mode", headers=headers)).status == 200
        assert (await client.get("/suspended", headers=headers)).status == 200
        assert (await client.get("/watchdog", headers=headers)).status == 503
        assert (
            await client.post("/watchdog/ack", headers=headers, json={"key": "x"})
        ).status == 503
        assert api._inflight_count == 0
        assert api._inflight_idle.is_set()


@pytest.mark.asyncio
async def test_http_job_routes_validate_errors_and_idempotent_submission():
    class TestStore(Store):
        def __init__(self):
            self.jobs = []

        async def list_recent(self, **kwargs):
            return self.jobs

        async def get(self, job_id):
            return next((j for j in self.jobs if j.id == job_id), None)

        async def list_events(self, job_id, *, limit):
            return [{"job_id": job_id, "limit": limit}]

        async def find_by_idempotency_key(self, *_args):
            return None

    store = TestStore()
    scheduler = Scheduler()

    async def submit(job):
        store.jobs.append(job)
        return job

    scheduler.submit = submit
    api = make_api(token="t", modes=Modes(), scheduler=scheduler, store=store)
    app = api_module.web.Application(
        middlewares=[
            api._error_middleware,
            api._auth_middleware,
            api._inflight_middleware,
        ]
    )
    api._install_routes(app)
    h = {"Authorization": "Bearer t"}
    async with TestClient(TestServer(app)) as client:
        assert (await client.get("/jobs?limit=no", headers=h)).status == 400
        assert (await client.get("/jobs?state=invalid", headers=h)).status == 400
        assert (await client.post("/jobs", headers=h, data="not-json")).status == 400
        assert (await client.post("/jobs", headers=h, json=[])).status == 400
        assert (
            await client.post(
                "/jobs",
                headers=h,
                json={"adapter": "ollama", "payload": {"prompt": "x"}},
            )
        ).status == 201
        job_id = store.jobs[0].id
        assert (await client.get("/jobs", headers=h)).status == 200
        assert (await client.get(f"/jobs/{job_id}", headers=h)).status == 200
        assert (
            await client.get(f"/jobs/{job_id}/events?limit=2", headers=h)
        ).status == 200
        assert (await client.get("/jobs/missing", headers=h)).status == 404
        assert (await client.get("/queue?limit=2", headers=h)).status == 200
        assert (await client.get("/vram", headers=h)).status == 200
        assert (
            await client.post(f"/jobs/{job_id}/cancel", headers=h, json={"force": True})
        ).status == 200


@pytest.mark.asyncio
async def test_http_mode_and_watchdog_actions():
    class Result:
        success = True
        from_mode = SimpleNamespace(value="ai")
        to_mode = SimpleNamespace(value="image")
        elapsed_s = 0.5
        suspended_count = 1
        interrupted_job_id = None
        error = None

    class ModesFull(Modes):
        async def set_mode(self, *args, **kwargs):
            return Result()

        async def resume_previous(self, **kwargs):
            return Result()

        async def clear_safety_halt(self, **kwargs):
            self.cleared = kwargs

        async def get_suspended(self):
            return [{"id": "s1"}]

        async def cancel_suspended(self, job_id):
            return job_id == "s1"

    class Watchdog:
        async def snapshot(self):
            return {"signals": []}

        async def acknowledge(self, key):
            self.acked = key

    modes, watchdog = ModesFull(), Watchdog()
    api = make_api(token="t", modes=modes, watchdog=watchdog)
    app = api_module.web.Application(
        middlewares=[
            api._error_middleware,
            api._auth_middleware,
            api._inflight_middleware,
        ]
    )
    api._install_routes(app)
    h = {"Authorization": "Bearer t"}
    async with TestClient(TestServer(app)) as client:
        assert (await client.post("/mode", headers=h, json={})).status == 400
        assert (
            await client.post("/mode", headers=h, json={"mode": "image"})
        ).status == 200
        assert (await client.post("/mode/resume", headers=h, json={})).status == 200
        assert (
            await client.post(
                "/mode/clear-halt", headers=h, json={"reason": "operator"}
            )
        ).status == 200
        assert modes.cleared["reason"] == "operator"
        assert (await client.post("/suspended/s1/cancel", headers=h)).status == 200
        assert (await client.post("/suspended/no/cancel", headers=h)).status == 404
        assert (await client.get("/watchdog", headers=h)).status == 200
        assert (
            await client.post("/watchdog/ack", headers=h, json={"key": "heat"})
        ).status == 200
        assert watchdog.acked == "heat"
        assert (await client.post("/watchdog/ack", headers=h, json={})).status == 400


@pytest.mark.asyncio
async def test_api_unix_lifecycle_and_startup_failures(tmp_path, monkeypatch):
    class UnixSite:
        def __init__(self, _runner, path):
            self.path = path

        async def start(self):
            from pathlib import Path

            Path(self.path).touch()

    monkeypatch.setattr(api_module.web, "UnixSite", UnixSite)
    socket_path = tmp_path / "api" / "scheduler.sock"
    api = SchedulerAPI(
        {"api_socket_path": str(socket_path), "shutdown_grace_seconds": 0.2},
        scheduler=Scheduler(),
        job_store=Store(),
        priority_manager=PriorityQueue(),
        vram_manager=Snapshot(),
        gpu_monitor=Monitor(),
    )
    assert api.listening_on is None
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    socket_path.write_text("stale socket placeholder", encoding="utf-8")
    await api.start()
    assert socket_path.exists()
    assert socket_path.stat().st_mode & 0o777 == 0o660
    assert api.listening_on == f"unix:{socket_path}"
    with pytest.raises(RuntimeError, match="already started"):
        await api.start()
    await api.stop()
    await api.stop()
    assert api.listening_on is None

    await api.start()
    api._inflight_idle.clear()
    api._shutdown_grace = 0
    await api.stop()

    missing = SchedulerAPI(
        {},
        scheduler=Scheduler(),
        job_store=Store(),
        priority_manager=PriorityQueue(),
        vram_manager=Snapshot(),
        gpu_monitor=Monitor(),
    )
    with pytest.raises(RuntimeError, match="neither api_socket_path"):
        await missing.start()
    assert missing._runner is None
    no_token = SchedulerAPI(
        {"api_bind": "127.0.0.1:8080"},
        scheduler=Scheduler(),
        job_store=Store(),
        priority_manager=PriorityQueue(),
        vram_manager=Snapshot(),
        gpu_monitor=Monitor(),
    )
    with pytest.raises(RuntimeError, match="api_token is missing"):
        await no_token.start()
    assert no_token._runner is None


@pytest.mark.asyncio
async def test_tcp_start_rejects_invalid_bind_shapes():
    api = make_api(token="secret")
    api._runner = object()
    api._bind = ":8080"
    with pytest.raises(RuntimeError, match="invalid api_bind"):
        await api._start_tcp()
    api._bind = "localhost:not-a-port"
    with pytest.raises(ValueError):
        await api._start_tcp()


@pytest.mark.asyncio
async def test_health_severity_and_job_submission_failure_paths():
    class ModesRisk(Modes):
        async def get_state(self):
            return {"mode": "gaming", "safety_halted": True}

    class WatchdogWarn:
        async def snapshot(self):
            return {"signals": [{"severity": "warn"}]}

    scheduler = Scheduler()
    scheduler.is_shutting_down = True
    api = make_api(
        token="t", modes=ModesRisk(), watchdog=WatchdogWarn(), scheduler=scheduler
    )
    app = api_module.web.Application(
        middlewares=[
            api._error_middleware,
            api._auth_middleware,
            api._inflight_middleware,
        ]
    )
    api._install_routes(app)
    async with TestClient(TestServer(app)) as client:
        health = await client.get("/health")
        assert health.status == 503
        assert (await health.json())["watchdog_severity"] == "critical"

    class ExistingStore(Store):
        existing = None

        async def find_by_idempotency_key(self, *_args):
            return self.existing

    store = ExistingStore()
    api = make_api(token="t", scheduler=Scheduler(), store=store)
    app = api_module.web.Application(
        middlewares=[
            api._error_middleware,
            api._auth_middleware,
            api._inflight_middleware,
        ]
    )
    api._install_routes(app)
    headers = {"Authorization": "Bearer t"}
    payload = {"adapter": "ollama", "payload": {}, "idempotency_key": "same"}
    async with TestClient(TestServer(app)) as client:
        # Store errors are logged and submission proceeds rather than failing.
        async def lookup_error(*_args):
            raise RuntimeError("index unavailable")

        store.find_by_idempotency_key = lookup_error
        assert (await client.post("/jobs", headers=headers, json=payload)).status == 201

        async def shutdown(_job):
            raise SchedulerShuttingDown("draining")

        api._scheduler.submit = shutdown
        assert (await client.post("/jobs", headers=headers, json=payload)).status == 503

        async def scheduler_error(_job):
            raise SchedulerError("unknown adapter")

        api._scheduler.submit = scheduler_error
        assert (await client.post("/jobs", headers=headers, json=payload)).status == 400

        async def unexpected(_job):
            raise RuntimeError("broken")

        api._scheduler.submit = unexpected
        assert (await client.post("/jobs", headers=headers, json=payload)).status == 500

        store.existing = api_module._job_from_body(payload)

        async def find_existing(*_args):
            return store.existing

        store.find_by_idempotency_key = find_existing
        api._scheduler.submit = lambda _job: asyncio.sleep(0, result=_job)
        response = await client.post("/jobs", headers=headers, json=payload)
        assert response.status == 200
        assert response.headers["Location"] == f"/jobs/{store.existing.id}"


@pytest.mark.asyncio
async def test_cancel_job_errors_suspended_fallback_and_optional_modes():
    class StatefulStore(Store):
        job = None

        async def get(self, _job_id):
            return self.job

    store = StatefulStore()
    scheduler = Scheduler()

    async def no_cancel(*_args, **_kwargs):
        return False

    scheduler.cancel = no_cancel
    modes = Modes()
    modes.cancel_suspended = lambda _job_id: asyncio.sleep(0, result=True)
    api = make_api(token="t", scheduler=scheduler, store=store, modes=modes)
    app = api_module.web.Application(
        middlewares=[
            api._error_middleware,
            api._auth_middleware,
            api._inflight_middleware,
        ]
    )
    api._install_routes(app)
    headers = {"Authorization": "Bearer t"}
    async with TestClient(TestServer(app)) as client:
        response = await client.post("/jobs/id/cancel?force=yes", headers=headers)
        assert response.status == 200
        assert (await response.json())["force"] is True
        modes.cancel_suspended = lambda _job_id: asyncio.sleep(0, result=False)
        assert (
            await client.post("/jobs/missing/cancel", headers=headers)
        ).status == 404
        store.job = api_module._job_from_body({"adapter": "ollama", "payload": {}})
        store.job.state = JobState.COMPLETED
        assert (
            await client.post(f"/jobs/{store.job.id}/cancel", headers=headers)
        ).status == 409

        async def not_cancellable(*_args, **_kwargs):
            raise JobNotCancellable("running")

        scheduler.cancel = not_cancellable
        assert (await client.post("/jobs/id/cancel", headers=headers)).status == 409

        async def broken_cancel(*_args, **_kwargs):
            raise RuntimeError("bad")

        scheduler.cancel = broken_cancel
        assert (await client.post("/jobs/id/cancel", headers=headers)).status == 500

        # Optional endpoints are guarded when their components are absent.
        no_modes = make_api(token="t")
        app2 = api_module.web.Application(
            middlewares=[
                no_modes._error_middleware,
                no_modes._auth_middleware,
                no_modes._inflight_middleware,
            ]
        )
        no_modes._install_routes(app2)
        async with TestClient(TestServer(app2)) as client2:
            assert (await client2.get("/mode", headers=headers)).status == 503
            assert (await client2.post("/mode/resume", headers=headers)).status == 503
            assert (
                await client2.post(
                    "/mode/clear-halt", headers=headers, json={"reason": "x"}
                )
            ).status == 503


@pytest.mark.asyncio
async def test_error_middleware_normalizes_http_and_unexpected_errors():
    api = make_api()
    app = api_module.web.Application(middlewares=[api._error_middleware])

    async def missing(_request):
        raise api_module.web.HTTPNotFound(reason="missing")

    async def broken(_request):
        raise RuntimeError("endpoint broke")

    app.router.add_get("/missing", missing)
    app.router.add_get("/broken", broken)
    async with TestClient(TestServer(app)) as client:
        missing_response = await client.get("/missing")
        assert missing_response.status == 404
        assert (await missing_response.json())["error"]["message"] == "missing"
        broken_response = await client.get("/broken")
        assert broken_response.status == 500
        assert "endpoint broke" in (await broken_response.json())["error"]["message"]


@pytest.mark.asyncio
async def test_remaining_api_error_and_optional_component_paths():
    assert str(APIError(400, "bad request")) == "bad request"

    class BrokenModes:
        async def get_state(self):
            raise RuntimeError("mode status failed")

        async def set_mode(self, *_args, **_kwargs):
            raise RuntimeError("transition failed")

        async def cancel_suspended(self, _job_id):
            raise RuntimeError("suspended cancellation failed")

    class BrokenWatchdog:
        async def snapshot(self):
            raise RuntimeError("watchdog status failed")

    api = make_api(
        token="secret", modes=BrokenModes(), watchdog=BrokenWatchdog()
    )

    async def not_cancelled(*_args, **_kwargs):
        return False

    api._scheduler.cancel = not_cancelled
    app = api_module.web.Application(
        middlewares=[
            api._error_middleware,
            api._auth_middleware,
            api._inflight_middleware,
        ]
    )
    api._install_routes(app)
    headers = {"Authorization": "Bearer secret"}
    async with TestClient(TestServer(app)) as client:
        health = await client.get("/health")
        assert health.status == 200
        status = await client.get("/status", headers=headers)
        assert status.status == 200
        assert "watchdog" in await status.json()

        transition = await client.post(
            "/mode", headers=headers, json={"mode": "image", "reason": "test"}
        )
        assert transition.status == 400

        bad_shape = await client.post("/jobs", headers=headers, json=[])
        assert bad_shape.status == 400
        invalid_job = await client.post(
            "/jobs",
            headers=headers,
            json={"adapter": "ollama", "payload": [], "id": "invalid"},
        )
        assert invalid_job.status == 400

        suspended = await client.post(
            "/jobs/suspended/cancel", headers=headers, json={}
        )
        assert suspended.status == 404

    class ExistingStore:
        async def get(self, _job_id):
            return Job(adapter="ollama", payload={}, id="active")

    scheduler = Scheduler()

    async def cannot_cancel(*_args, **_kwargs):
        return False

    scheduler.cancel = cannot_cancel
    api2 = make_api(token="secret", scheduler=scheduler, store=ExistingStore())
    app2 = api_module.web.Application(
        middlewares=[
            api2._error_middleware,
            api2._auth_middleware,
            api2._inflight_middleware,
        ]
    )
    api2._install_routes(app2)
    async with TestClient(TestServer(app2)) as client:
        response = await client.post("/jobs/active/cancel", headers=headers, json={})
        assert response.status == 409


@pytest.mark.asyncio
async def test_api_socket_chmod_fallback_tcp_start_and_middleware_cancel(
    tmp_path, monkeypatch
):
    from pathlib import Path

    from aiohttp.test_utils import make_mocked_request

    api = make_api(token="secret")
    api._bind = None
    api._socket_path = str(tmp_path / "api.sock")

    def fail_chmod(_path, _mode):
        raise OSError("permissions unavailable")

    monkeypatch.setattr(Path, "chmod", fail_chmod)
    await api.start()
    assert api.listening_on.startswith("unix:")
    await api.stop()
    monkeypatch.undo()

    tcp_api = make_api(token="secret")
    tcp_api._socket_path = None
    tcp_api._bind = "127.0.0.1:0"
    await tcp_api.start()
    assert tcp_api.listening_on == "http://127.0.0.1:0"
    await tcp_api.stop()

    request = make_mocked_request("GET", "/status")

    async def allowed(_request):
        return api_module.web.Response(text="ok")

    assert (await api._auth_middleware(request, allowed)).status == 200
    api._bind = "127.0.0.1:8080"
    api._token = None
    assert (await api._auth_middleware(request, allowed)).status == 503

    request = make_mocked_request("GET", "/cancelled")

    async def cancelled(_request):
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await api._error_middleware(request, cancelled)
