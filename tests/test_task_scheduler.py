"""Tests for the :mod:`monkey_head.core.task_scheduler` module."""

from __future__ import annotations

from pathlib import Path
import sys
import types

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

from monkey_head.core.task_scheduler import (  # noqa: E402  pylint: disable=wrong-import-position
    Agent,
    ResourceProfile,
    ResourceSnapshot,
    TaskPriority,
    TaskScheduler,
    TaskStatus,
)


def _healthy_snapshot() -> ResourceSnapshot:
    return ResourceSnapshot(
        cpu_percent=12.0,
        memory_available=8 * 1024**3,
        memory_total=16 * 1024**3,
        battery_percent=80.0,
    )


def _overloaded_snapshot() -> ResourceSnapshot:
    return ResourceSnapshot(
        cpu_percent=97.0,
        memory_available=1 * 1024**3,
        memory_total=16 * 1024**3,
        battery_percent=15.0,
    )


def test_submit_task_dispatches_when_resources_are_healthy():
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)

    record = scheduler.submit_task(command="run diagnostics")

    assert record.status is TaskStatus.RUNNING
    assert record.assigned_agent in {Agent.SPARK, Agent.ZAP}
    assert record.attempts == 1


def test_submit_task_is_pending_when_resources_are_constrained():
    scheduler = TaskScheduler(health_provider=_overloaded_snapshot)

    record = scheduler.submit_task(command="train model", priority=TaskPriority.CRITICAL)

    assert record.status is TaskStatus.PENDING
    assert record.assigned_agent is None
    assert record.attempts == 0


def test_fail_task_reassigns_to_alternate_agent():
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)

    record = scheduler.submit_task(
        command="analyze telemetry",
        requested_agent=Agent.SPARK,
        resource_profile=ResourceProfile(cpu=0.2, memory=0.1, battery=0.1),
    )

    assert record.assigned_agent is Agent.SPARK

    failed = scheduler.fail_task(record.task_id, "transient GPU fault")

    assert failed.status is TaskStatus.RUNNING
    assert failed.assigned_agent is Agent.ZAP
    assert failed.attempts == 2
