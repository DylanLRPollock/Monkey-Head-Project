# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Task Scheduler module (tests)

"""Tests for the :mod:`hueyos.core.task_scheduler` module."""

from __future__ import annotations

import sys
import types
from pathlib import Path

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

from hueyos.core.task_scheduler import (  # noqa: E402  pylint: disable=wrong-import-position
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

    record = scheduler.schedule_task(
        command="train model", priority=TaskPriority.CRITICAL
    )

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


def test_complete_task_records_result_and_history():
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)

    record = scheduler.schedule_task(
        command="collect logs", requested_agent=Agent.SPARK
    )
    assert record.status is TaskStatus.RUNNING

    completed = scheduler.complete_task(record.task_id, result={"ok": True})

    assert completed.status is TaskStatus.COMPLETED
    assert completed.result == {"ok": True}
    assert any(entry.status is TaskStatus.COMPLETED for entry in completed.history)


def test_cancel_task_frees_capacity_and_logs_reason():
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)

    running = scheduler.schedule_task(command="initial", requested_agent=Agent.SPARK)
    assert running.assigned_agent is Agent.SPARK

    cancelled = scheduler.cancel_task(running.task_id, reason="operator request")
    assert cancelled.status is TaskStatus.CANCELLED
    assert cancelled.error == "operator request"
    assert any(entry.status is TaskStatus.CANCELLED for entry in cancelled.history)

    follow_up = scheduler.schedule_task(command="follow", requested_agent=Agent.SPARK)
    assert follow_up.status is TaskStatus.RUNNING
    assert follow_up.assigned_agent is Agent.SPARK


def test_list_tasks_supports_status_filters():
    scheduler = TaskScheduler(
        health_provider=_healthy_snapshot,
        max_concurrency={Agent.SPARK: 1, Agent.ZAP: 0},
    )

    running = scheduler.schedule_task(command="active", requested_agent=Agent.SPARK)
    pending = scheduler.schedule_task(
        command="waiting",
        priority=TaskPriority.HIGH,
        requested_agent=Agent.SPARK,
    )

    subset = scheduler.list_tasks(statuses=[TaskStatus.PENDING])

    assert {task.task_id for task in subset} == {pending.task_id}
    assert running.task_id not in {task.task_id for task in subset}
