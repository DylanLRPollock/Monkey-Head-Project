# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Api Routes module (tests)

"""Tests for FastAPI application routes."""

from __future__ import annotations

import asyncio
import sys
import types
from pathlib import Path
from typing import Any

import importlib

import pytest

from httpx import ASGITransport, AsyncClient

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO_ROOT))
sys.path.append(str(REPO_ROOT / "src"))

if "huey" not in sys.modules:
    huey_pkg = types.ModuleType("huey")
    huey_pkg.__path__ = [
        str(REPO_ROOT / "src" / "huey"),
        str(REPO_ROOT / "huey"),
    ]
    sys.modules["huey"] = huey_pkg
else:
    pkg = sys.modules["huey"]
    current_path = list(getattr(pkg, "__path__", []))
    for candidate in (REPO_ROOT / "src" / "huey", REPO_ROOT / "huey"):
        candidate_str = str(candidate)
        if candidate_str not in current_path:
            current_path.append(candidate_str)
    pkg.__path__ = current_path

if "huey.memory" not in sys.modules:
    memory_pkg = types.ModuleType("huey.memory")
    memory_pkg.__path__ = [str(REPO_ROOT / "huey" / "memory")]
    sys.modules["huey.memory"] = memory_pkg
else:
    memory_pkg = sys.modules["huey.memory"]

py_pkg = types.ModuleType("huey.memory.PY")
py_pkg.__path__ = [str(REPO_ROOT / "huey" / "memory" / "PY")]
sys.modules["huey.memory.PY"] = py_pkg
setattr(memory_pkg, "PY", py_pkg)

api_module = importlib.import_module("huey.api")

# Import the public API symbols used by these tests directly into the module
# namespace for convenience and to mirror the FastAPI application's exports.
from hueyos.core.task_scheduler import ResourceSnapshot, TaskScheduler, TaskStatus
from hueyos.hardware.plugins import SensorReading

ai_module = types.ModuleType("huey.memory.PY.ai_processor")


class _DummyAIProcessor:
    def process_data(self, text: str) -> str:
        return text

    def compute_mean(self, numbers: list[float]) -> float:
        return sum(numbers) / len(numbers) if numbers else 0.0

    def analyze_data(self, text: str) -> dict[str, int]:
        return {"length": len(text)}


ai_module.AIProcessor = _DummyAIProcessor  # type: ignore[attr-defined]
sys.modules["huey.memory.PY.ai_processor"] = ai_module
setattr(py_pkg, "ai_processor", ai_module)

@pytest.mark.asyncio
async def test_healthz_endpoint_returns_service_status():
    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "hueyos"}


@pytest.mark.asyncio
async def test_api_token_is_required_when_configured(monkeypatch):
    monkeypatch.setenv("HUEY_API_TOKEN", "test-token")

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        health = await client.get("/healthz")
        blocked = await client.get("/tasks")
        allowed = await client.get(
            "/tasks",
            headers={"Authorization": "Bearer test-token"},
        )

    assert health.status_code == 200
    assert blocked.status_code == 401
    assert allowed.status_code == 200


def test_api_startup_fails_without_token_in_non_development_env(monkeypatch):
    monkeypatch.setenv("HUEY_ENV", "production")
    monkeypatch.delenv("HUEY_API_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="HUEY_API_TOKEN must be set"):
        importlib.reload(api_module)


def test_api_startup_fails_with_placeholder_token_in_non_development_env(monkeypatch):
    monkeypatch.setenv("HUEY_ENV", "staging")
    monkeypatch.setenv("HUEY_API_TOKEN", "change-me")

    with pytest.raises(RuntimeError, match="HUEY_API_TOKEN must be set"):
        importlib.reload(api_module)


def test_api_startup_allows_missing_token_in_development_env(monkeypatch):
    monkeypatch.setenv("HUEY_ENV", "development")
    monkeypatch.delenv("HUEY_API_TOKEN", raising=False)

    reloaded = importlib.reload(api_module)
    assert reloaded.app is not None


def _healthy_snapshot() -> ResourceSnapshot:
    return ResourceSnapshot(
        cpu_percent=10.0,
        memory_available=8 * 1024**3,
        memory_total=16 * 1024**3,
        battery_percent=80.0,
    )


def _degraded_snapshot() -> ResourceSnapshot:
    return ResourceSnapshot(
        cpu_percent=98.0,
        memory_available=512 * 1024**2,
        memory_total=16 * 1024**3,
        battery_percent=10.0,
    )


@pytest.mark.asyncio
async def test_task_management_endpoints_support_submission_and_cancellation(
    monkeypatch,
):
    monkeypatch.setenv("HUEY_ENABLE_UNSAFE_TASKS", "true")
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)
    monkeypatch.setattr(api_module, "SCHEDULER", scheduler, raising=False)

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        submit = await client.post("/tasks", json={"command": "calibrate sensors"})
        assert submit.status_code == 202
        payload = submit.json()
        task_id = payload["task_id"]
        assert payload["status"] == TaskStatus.RUNNING.value

        listing = await client.get("/tasks")
        assert listing.status_code == 200
        list_payload = listing.json()
        assert list_payload["tasks"]

        detail = await client.get(f"/tasks/{task_id}")
        assert detail.status_code == 200
        assert detail.json()["task_id"] == task_id

        cancel = await client.post(f"/tasks/{task_id}/cancel")
        assert cancel.status_code == 202
        assert cancel.json()["status"] == TaskStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_task_submission_respects_resource_constraints(monkeypatch):
    monkeypatch.setenv("HUEY_ENABLE_UNSAFE_TASKS", "true")
    scheduler = TaskScheduler(health_provider=_degraded_snapshot)
    monkeypatch.setattr(api_module, "SCHEDULER", scheduler, raising=False)

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        submit = await client.post("/tasks", json={"command": "train heavy model"})

    assert submit.status_code == 202
    assert submit.json()["status"] == TaskStatus.PENDING.value


@pytest.mark.asyncio
async def test_task_and_dashboard_surfaces_block_remote_when_token_unset(monkeypatch):
    monkeypatch.delenv("HUEY_API_TOKEN", raising=False)
    monkeypatch.delenv("HUEY_ENABLE_UNSAFE_TASKS", raising=False)
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)
    monkeypatch.setattr(api_module, "SCHEDULER", scheduler, raising=False)

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://198.51.100.10") as client:
        submit = await client.post("/tasks", json={"command": "calibrate sensors"})
        dashboard = await client.get("/dashboard")

    assert submit.status_code == 403
    assert dashboard.status_code == 403


@pytest.mark.asyncio
async def test_task_submission_denied_by_default_without_unsafe_flag(monkeypatch):
    monkeypatch.delenv("HUEY_API_TOKEN", raising=False)
    monkeypatch.delenv("HUEY_ENABLE_UNSAFE_TASKS", raising=False)
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)
    monkeypatch.setattr(api_module, "SCHEDULER", scheduler, raising=False)

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        submit = await client.post("/tasks", json={"command": "echo secret-token"})

    assert submit.status_code == 403
    assert "disabled" in submit.json()["detail"].lower()


@pytest.mark.asyncio
async def test_task_submission_allowed_for_development_with_unsafe_flag(monkeypatch):
    monkeypatch.delenv("HUEY_API_TOKEN", raising=False)
    monkeypatch.setenv("HUEY_ENABLE_UNSAFE_TASKS", "true")
    monkeypatch.setenv("HUEY_ENV", "development")
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)
    monkeypatch.setattr(api_module, "SCHEDULER", scheduler, raising=False)

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        submit = await client.post("/tasks", json={"command": "calibrate sensors"})

    assert submit.status_code == 202


@pytest.mark.asyncio
async def test_task_submission_requires_unsafe_flag_even_when_authenticated(monkeypatch):
    monkeypatch.setenv("HUEY_API_TOKEN", "test-token")
    monkeypatch.setenv("HUEY_ENV", "production")
    monkeypatch.delenv("HUEY_ENABLE_UNSAFE_TASKS", raising=False)
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)
    monkeypatch.setattr(api_module, "SCHEDULER", scheduler, raising=False)

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        denied = await client.post(
            "/tasks",
            json={"command": "calibrate sensors"},
            headers={"Authorization": "Bearer test-token"},
        )

    assert denied.status_code == 403
    monkeypatch.setenv("HUEY_ENABLE_UNSAFE_TASKS", "true")
    transport2 = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport2, base_url="http://testserver") as client:
        enabled = await client.post(
            "/tasks",
            json={"command": "calibrate sensors"},
            headers={"Authorization": "Bearer test-token"},
        )

    assert enabled.status_code == 202


@pytest.mark.asyncio
async def test_system_status_endpoint_reports_expected_fields(monkeypatch, tmp_path):
    memory_root = tmp_path / "memory"
    memory_root.mkdir()

    monkeypatch.setattr(
        api_module.platform,
        "uname",
        lambda: types.SimpleNamespace(
            system="TestOS",
            release="1.0",
            version="1.0.0",
            machine="x86_64",
        ),
    )
    monkeypatch.setattr(api_module.platform, "python_version", lambda: "3.12.1")
    monkeypatch.setattr(api_module.socket, "gethostname", lambda: "huey-node")
    monkeypatch.setattr(api_module.time, "time", lambda: 200.0)
    monkeypatch.setattr(
        api_module.shutil,
        "disk_usage",
        lambda path: types.SimpleNamespace(free=123456),
    )
    fake_psutil = types.SimpleNamespace(
        cpu_count=lambda logical=True: 8,
        virtual_memory=lambda: types.SimpleNamespace(
            total=16 * 1024**3, available=8 * 1024**3
        ),
        boot_time=lambda: 100.0,
    )
    monkeypatch.setattr(api_module, "psutil", fake_psutil)
    monkeypatch.setattr(api_module, "get_memory_path", lambda create=True: memory_root)

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/system/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["system"] == "TestOS"
    assert payload["cpu_count"] == 8
    assert payload["memory_total"] == 16 * 1024**3
    assert payload["memory_available"] == 8 * 1024**3
    assert payload["disk_free"] == 123456
    assert payload["memory_path"] == str(memory_root)


@pytest.mark.asyncio
async def test_resilience_endpoints_support_manual_override(monkeypatch):
    from hueyos.core.resilience import CrashRecoveryManager

    manager = CrashRecoveryManager()
    monkeypatch.setattr(api_module, "CRASH_MANAGER", manager, raising=False)

    state = {"healthy": False, "restarts": 0}

    def health_check() -> bool:
        return state["healthy"]

    def restart() -> None:
        state["restarts"] += 1
        state["healthy"] = True

    manager.register_process("core-loop", health_check=health_check, restart=restart)

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        state["healthy"] = False
        poll = await client.post("/resilience/poll")
        assert poll.status_code == 200
        assert poll.json()["events"][0]["restarted"] is True

        override = await client.post(
            "/resilience/monitors/core-loop/override",
            json={"auto_restart": False, "reason": "maintenance"},
        )
        assert override.status_code == 200
        payload = override.json()
        assert payload["auto_restart"] is False
        assert payload["manual_override_reason"] == "maintenance"

        state["healthy"] = False
        second_poll = await client.post("/resilience/poll")
        assert second_poll.status_code == 200
        assert second_poll.json()["events"][0]["restarted"] is False

        manual = await client.post("/resilience/monitors/core-loop/restart")
        assert manual.status_code == 200
        assert manual.json()["restart_attempts"] >= 2


@pytest.mark.asyncio
async def test_emergency_endpoints_require_quorum(monkeypatch):
    from hueyos.core.resilience import EmergencyGovernanceController

    controller = EmergencyGovernanceController()
    controller.register_service("mock", stop=lambda: None, start=lambda: None)
    monkeypatch.setattr(api_module, "EMERGENCY_CONTROLLER", controller, raising=False)

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        status_response = await client.get("/governance/emergency/status")
        assert status_response.status_code == 200
        assert status_response.json()["state"] == "normal"

        denied = await client.post(
            "/governance/emergency/enter",
            json={"triggered_by": "spark", "reason": "test"},
        )
        assert denied.status_code == 403

        entered = await client.post(
            "/governance/emergency/enter",
            json={"triggered_by": "spark", "reason": "grid", "approvals": ["zap"]},
        )
        assert entered.status_code == 200
        assert entered.json()["state"] == "emergency"


@pytest.mark.asyncio
async def test_sensor_network_and_power_endpoints(monkeypatch, tmp_path):
    from hueyos.hardware import drivers
    from hueyos.hardware.manager import SensorManager
    from hueyos.hardware.plugins import SensorRegistry
    from hueyos.honeycomb.storage import HoneycombStorage
    from hueyos.network.manager import NetworkStatus
    from hueyos.power.management import PowerEvent

    storage = HoneycombStorage(base_dir=tmp_path)
    registry = SensorRegistry()
    drivers.register_builtin_sensors(registry)
    sensor_manager = SensorManager(storage=storage, registry=registry)
    monkeypatch.setattr(api_module, "SENSOR_MANAGER", sensor_manager, raising=False)

    class DummyNetworkManager:
        def __init__(self) -> None:
            self.status = NetworkStatus(
                active_interface="eth0",
                interfaces={"eth0": {"isup": 1.0, "speed": 1000.0, "duplex": 1.0}},
                wired_available=True,
                wifi_available=False,
                connected=True,
                last_checked=123.0,
            )

        def check_status(self) -> NetworkStatus:
            return self.status

        def ensure_connectivity(self) -> NetworkStatus:
            return self.status

    monkeypatch.setattr(
        api_module, "NETWORK_MANAGER", DummyNetworkManager(), raising=False
    )

    class DummyBatteryMonitor:
        shutdown_threshold = 5.0

        def get_status(self) -> dict[str, float | bool | None]:
            return {
                "percent": 42.0,
                "secs_left": 1200.0,
                "power_plugged": False,
                "estimated_runtime_minutes": 20.0,
            }

        def should_shutdown(self) -> bool:
            return False

        def initiate_shutdown(self) -> PowerEvent:
            return PowerEvent(
                timestamp=456.0, action="shutdown", metadata={"initiated": True}
            )

    monkeypatch.setattr(
        api_module, "BATTERY_MONITOR", DummyBatteryMonitor(), raising=False
    )

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        sensors_initial = await client.get("/sensors")
        assert sensors_initial.status_code == 200
        assert sensors_initial.json()["sensors"] == []

        registration = await client.post(
            "/sensors/register",
            json={
                "name": "dev-entropy",
                "plugin": "virtual.random",
                "config": {"precision": 2},
            },
        )
        assert registration.status_code == 201

        poll_response = await client.post("/sensors/dev-entropy/poll")
        assert poll_response.status_code == 200
        poll_payload = poll_response.json()
        assert poll_payload["name"] == "dev-entropy"
        assert "timestamp" in poll_payload

        history = await client.get("/sensors/dev-entropy/history", params={"limit": 5})
        assert history.status_code == 200
        history_payload = history.json()
        assert history_payload["sensor"] == "dev-entropy"
        assert history_payload["readings"]

        plugins = await client.get("/sensors/plugins")
        assert plugins.status_code == 200
        assert "virtual.random" in plugins.json()["plugins"]

        net_status = await client.get("/network/status")
        assert net_status.status_code == 200
        assert net_status.json()["active_interface"] == "eth0"

        net_ensure = await client.post("/network/ensure")
        assert net_ensure.status_code == 200

        battery = await client.get("/power/battery")
        assert battery.status_code == 200
        assert battery.json()["percent"] == 42.0

        should_shutdown = await client.get("/power/should-shutdown")
        assert should_shutdown.status_code == 200
        assert should_shutdown.json()["should_shutdown"] is False

        shutdown = await client.post("/power/shutdown")
        assert shutdown.status_code == 200
        assert shutdown.json()["metadata"]["initiated"] is True

        authorised = await client.post(
            "/governance/emergency/action",
            json={"actor": "spark", "approvals": ["zap"], "action": "shed-load"},
        )
        assert authorised.status_code == 200
        assert authorised.json()["status"] == "authorised"

        exited = await client.post(
            "/governance/emergency/exit",
            json={"requested_by": "spark", "approvals": ["zap"]},
        )
        assert exited.status_code == 200
        assert exited.json()["state"] == "normal"


class _StubSensorManager:
    def __init__(self) -> None:
        self.registry = object()
        self._sensors: dict[str, dict[str, Any]] = {}
        self._subscriptions: set[asyncio.Queue[SensorReading]] = set()

    def list_sensors(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "plugin": info["plugin"],
                "module": "dummy.module",
                "config": info["config"],
            }
            for name, info in self._sensors.items()
        ]

    def get_sensor(self, name: str | None) -> dict[str, Any] | None:
        if name is None:
            return None
        return self._sensors.get(name)

    def add_sensor(self, plugin: str, name: str, config: dict[str, Any]) -> None:
        if plugin != "dummy":
            raise KeyError(plugin)
        self._sensors[name] = {"plugin": plugin, "config": dict(config)}

    def poll_sensor(self, sensor_name: str) -> SensorReading:
        if sensor_name not in self._sensors:
            raise KeyError(sensor_name)
        return SensorReading(
            name=sensor_name,
            value={"payload": True},
            timestamp=1.0,
            provenance={"source": "stub"},
        )

    def poll_all(self) -> list[SensorReading]:
        return [self.poll_sensor(name) for name in self._sensors]

    def load_history(self, sensor_name: str, limit: int) -> list[dict[str, Any]]:
        self.poll_sensor(sensor_name)
        return [
            {
                "name": sensor_name,
                "value": {"payload": True},
                "timestamp": 1.0,
                "provenance": {"source": "stub"},
            }
        ]

    def subscribe(self, sensor_name: str | None) -> asyncio.Queue[SensorReading]:
        queue: asyncio.Queue[SensorReading] = asyncio.Queue()
        target = sensor_name or next(iter(self._sensors), "stub")
        queue.put_nowait(
            SensorReading(
                name=target,
                value={"payload": True},
                timestamp=1.0,
                provenance={"source": "stub"},
            )
        )
        self._subscriptions.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[SensorReading]) -> None:
        self._subscriptions.discard(queue)


@pytest.mark.asyncio
async def test_system_status_alias_endpoint(monkeypatch):
    stub_status = api_module.SystemStatusResponse(
        system="Linux",
        release="6.1",
        version="6.1",
        architecture="x86_64",
        hostname="huey-node",
        python_version="3.11",
        cpu_count=4,
        memory_total=1024,
        memory_available=512,
        uptime_seconds=12.0,
        boot_time=1.0,
        disk_free=2048,
        memory_path="/tmp/memory",
    )
    monkeypatch.setattr(
        api_module, "_build_system_status", lambda: stub_status, raising=False
    )

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/status/system")

    assert response.status_code == 200
    payload = response.json()
    assert payload["system"] == "Linux"
    assert payload["memory_path"] == "/tmp/memory"


@pytest.mark.asyncio
async def test_ai_process_text_supports_streaming_and_validation(monkeypatch):
    monkeypatch.setattr(
        api_module, "_stream_text", lambda text, chunk_size=64: [text], raising=False
    )

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/ai/process-text",
            json={"text": "hello world"},
            params={"stream": "true"},
        )
        assert response.status_code == 200
        assert response.json() == ["hello world"]

        invalid = await client.post("/ai/process-text", json={"text": "   "})

    assert invalid.status_code == 400
    assert "empty" in invalid.json()["detail"]


@pytest.mark.asyncio
async def test_ai_analyze_text_rejects_empty_payload():
    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/ai/analyze-text", json={"text": ""})

    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_sensor_streaming_and_invalid_registration(monkeypatch):
    stub_manager = _StubSensorManager()
    stub_manager.add_sensor("dummy", "alpha", {})
    monkeypatch.setattr(api_module, "SENSOR_MANAGER", stub_manager, raising=False)
    monkeypatch.setattr(
        api_module,
        "_sensor_stream",
        lambda sensor_name: [f"data: {sensor_name or 'alpha'}\n\n"],
        raising=False,
    )

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/sensors/alpha/stream")
        assert response.status_code == 200
        assert response.json() == ["data: alpha\n\n"]

        failure = await client.post(
            "/sensors/register",
            json={"name": "beta", "plugin": "unknown", "config": {}},
        )

    assert failure.status_code == 404


@pytest.mark.asyncio
async def test_telemetry_ai_recent_redacts_sensitive_fields(monkeypatch):
    from hueyos.utils.persistence import AIInteraction

    monkeypatch.setattr(
        api_module.TELEMETRY_STORE,
        "fetch_recent_ai_results",
        lambda limit=25: [
            AIInteraction(
                timestamp=1234.5,
                prompt="secret-token=ABC123",
                response="classified-output",
                model="llama3",
                backend="ollama",
                instruction="do secret thing",
                metadata={"secret": "value"},
                status="success",
            )
        ],
        raising=True,
    )

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/telemetry/ai/recent")

    assert response.status_code == 200
    payload = response.json()["records"][0]
    assert payload["prompt"] == "[redacted]"
    assert payload["response"] == "[redacted]"
    assert payload["instruction"] is None
    assert payload["metadata"] == {}


@pytest.mark.asyncio
async def test_dashboard_redacts_ai_prompts_and_responses(monkeypatch):
    from hueyos.utils.persistence import AIInteraction

    observed = {}

    def _capture_dashboard(system, battery, sensor_records, ai_records, catalog):
        observed["ai_records"] = ai_records
        return "dashboard"

    monkeypatch.setattr(api_module, "_render_dashboard", _capture_dashboard, raising=True)
    monkeypatch.setattr(
        api_module.TELEMETRY_STORE,
        "fetch_recent_sensor_readings",
        lambda limit=10: [],
        raising=True,
    )
    monkeypatch.setattr(
        api_module.TELEMETRY_STORE,
        "fetch_recent_ai_results",
        lambda limit=10: [
            AIInteraction(
                timestamp=1234.5,
                prompt="secret-token=ABC123",
                response="classified-output",
                model="llama3",
                backend="ollama",
                instruction="do secret thing",
                metadata={"secret": "value"},
                status="success",
            )
        ],
        raising=True,
    )

    transport = ASGITransport(app=api_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert getattr(payload, "content", None) == "dashboard"
    assert observed["ai_records"][0].prompt == "[redacted]"
    assert observed["ai_records"][0].response == "[redacted]"
    assert observed["ai_records"][0].instruction is None
    assert observed["ai_records"][0].metadata == {}
