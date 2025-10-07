"""Tests for FastAPI application routes."""

from __future__ import annotations

from pathlib import Path
import sys
import types

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

import huey.api as api_module
from huey.api import app
from monkey_head.core.task_scheduler import ResourceSnapshot, TaskScheduler, TaskStatus


@pytest.mark.asyncio
async def test_healthz_endpoint_returns_service_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "hueyos"}


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
async def test_task_management_endpoints_support_submission_and_cancellation(monkeypatch):
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)
    monkeypatch.setattr(api_module, "SCHEDULER", scheduler, raising=False)

    transport = ASGITransport(app=app)
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
    scheduler = TaskScheduler(health_provider=_degraded_snapshot)
    monkeypatch.setattr(api_module, "SCHEDULER", scheduler, raising=False)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        submit = await client.post("/tasks", json={"command": "train heavy model"})

    assert submit.status_code == 202
    assert submit.json()["status"] == TaskStatus.PENDING.value


@pytest.mark.asyncio
async def test_resilience_endpoints_support_manual_override(monkeypatch):
    from monkey_head.core.resilience import CrashRecoveryManager

    manager = CrashRecoveryManager()
    monkeypatch.setattr(api_module, "CRASH_MANAGER", manager, raising=False)

    state = {"healthy": False, "restarts": 0}

    def health_check() -> bool:
        return state["healthy"]

    def restart() -> None:
        state["restarts"] += 1
        state["healthy"] = True

    manager.register_process("core-loop", health_check=health_check, restart=restart)

    transport = ASGITransport(app=app)
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
    from monkey_head.core.resilience import EmergencyGovernanceController

    controller = EmergencyGovernanceController()
    controller.register_service("mock", stop=lambda: None, start=lambda: None)
    monkeypatch.setattr(api_module, "EMERGENCY_CONTROLLER", controller, raising=False)

    transport = ASGITransport(app=app)
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
