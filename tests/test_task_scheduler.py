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


def test_schedule_task_dispatches_when_resources_are_healthy():
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)

    record = scheduler.schedule_task(command="run diagnostics")

    assert record.status is TaskStatus.RUNNING
    assert record.assigned_agent in {Agent.SPARK, Agent.ZAP}
    assert record.attempts == 1


def test_schedule_task_is_pending_when_resources_are_constrained():
    scheduler = TaskScheduler(health_provider=_overloaded_snapshot)

    record = scheduler.schedule_task(command="train model", priority=TaskPriority.CRITICAL)

    assert record.status is TaskStatus.PENDING
    assert record.assigned_agent is None
    assert record.attempts == 0


def test_fail_task_reassigns_to_alternate_agent():
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)

    record = scheduler.schedule_task(
        command="analyze telemetry",
        requested_agent=Agent.SPARK,
        resource_profile=ResourceProfile(cpu=0.2, memory=0.1, battery=0.1),
    )

    assert record.assigned_agent is Agent.SPARK

    failed = scheduler.fail_task(record.task_id, "transient GPU fault")

    assert failed.status is TaskStatus.RUNNING
    assert failed.assigned_agent is Agent.ZAP
    assert failed.attempts == 2


def test_run_pending_dispatches_when_capacity_frees():
    scheduler = TaskScheduler(
        health_provider=_healthy_snapshot,
        max_concurrency={Agent.SPARK: 1, Agent.ZAP: 0},
    )

    first = scheduler.schedule_task(command="initial", requested_agent=Agent.SPARK)
    assert first.status is TaskStatus.RUNNING

    queued = scheduler.schedule_task(
        command="follow up",
        priority=TaskPriority.HIGH,
        requested_agent=Agent.SPARK,
    )
    assert queued.status is TaskStatus.PENDING

    scheduler.complete_task(first.task_id)

    refreshed = scheduler.get_task(queued.task_id)
    assert refreshed.status is TaskStatus.RUNNING
    assert refreshed.assigned_agent is Agent.SPARK


def test_priority_queue_runs_critical_work_first():
    scheduler = TaskScheduler(
        health_provider=_healthy_snapshot,
        max_concurrency={Agent.SPARK: 1, Agent.ZAP: 0},
    )

    active = scheduler.schedule_task(command="bootstrap", requested_agent=Agent.SPARK)
    assert active.status is TaskStatus.RUNNING

    low = scheduler.schedule_task(
        command="routine check",
        priority=TaskPriority.LOW,
        requested_agent=Agent.SPARK,
    )
    critical = scheduler.schedule_task(
        command="critical repair",
        priority=TaskPriority.CRITICAL,
        requested_agent=Agent.SPARK,
    )

    assert low.status is TaskStatus.PENDING
    assert critical.status is TaskStatus.PENDING

    scheduler.complete_task(active.task_id)

    assert scheduler.get_task(critical.task_id).status is TaskStatus.RUNNING
    assert scheduler.get_task(low.task_id).status is TaskStatus.PENDING


def test_run_pending_uses_updated_health_snapshot():
    state = {"healthy": False}

    def provider() -> ResourceSnapshot:
        return _healthy_snapshot() if state["healthy"] else _overloaded_snapshot()

    scheduler = TaskScheduler(
        health_provider=provider,
        max_concurrency={Agent.SPARK: 1, Agent.ZAP: 0},
    )

    record = scheduler.schedule_task(command="delayed", requested_agent=Agent.SPARK)
    assert record.status is TaskStatus.PENDING

    state["healthy"] = True
    dispatched = scheduler.run_pending()

    assert dispatched and dispatched[0].task_id == record.task_id
    assert scheduler.get_task(record.task_id).status is TaskStatus.RUNNING
