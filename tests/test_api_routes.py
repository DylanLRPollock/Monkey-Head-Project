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
