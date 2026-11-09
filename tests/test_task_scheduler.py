# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Task Scheduler module (tests)

"""Tests for the :mod:`huey.core.task_scheduler` module."""

from __future__ import annotations

from huey.core.task_scheduler import (
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
    assert record.history[-1].status is TaskStatus.RUNNING


def test_submit_task_remains_pending_when_resources_are_constrained():
    scheduler = TaskScheduler(health_provider=_overloaded_snapshot)

    record = scheduler.submit_task(
        command="train model", priority=TaskPriority.CRITICAL
    )

    assert record.status is TaskStatus.PENDING
    assert record.assigned_agent is None
    assert record.attempts == 0
    assert "exceeds" in record.history[-1].message


def test_fail_task_reassigns_to_alternate_agent():
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)

    record = scheduler.submit_task(
        command="analyze telemetry",
        requested_agent=Agent.SPARK,
        resource_profile=ResourceProfile(cpu=0.2, memory=0.1, battery=0.1),
    )
    failed_agent = record.assigned_agent
    assert failed_agent is Agent.SPARK

    retried = scheduler.fail_task(record.task_id, "transient GPU fault")

    assert retried.status is TaskStatus.RUNNING
    assert retried.assigned_agent is Agent.ZAP
    assert retried.attempts == 2
    assert retried.error == "transient GPU fault"


def test_reconcile_dispatches_pending_tasks_after_health_recovers():
    state = {"healthy": False}

    def provider() -> ResourceSnapshot:
        return _healthy_snapshot() if state["healthy"] else _overloaded_snapshot()

    scheduler = TaskScheduler(health_provider=provider)
    record = scheduler.submit_task(command="delayed", requested_agent=Agent.SPARK)
    assert record.status is TaskStatus.PENDING

    state["healthy"] = True
    dispatched = scheduler.reconcile()

    assert [task.task_id for task in dispatched] == [record.task_id]
    assert scheduler.get_task(record.task_id).status is TaskStatus.RUNNING


def test_reconcile_processes_pending_tasks_in_priority_order():
    state = {"healthy": False}

    def provider() -> ResourceSnapshot:
        return _healthy_snapshot() if state["healthy"] else _overloaded_snapshot()

    scheduler = TaskScheduler(health_provider=provider)
    low = scheduler.submit_task(command="routine", priority=TaskPriority.LOW)
    critical = scheduler.submit_task(command="repair", priority=TaskPriority.CRITICAL)
    assert low.status is critical.status is TaskStatus.PENDING

    state["healthy"] = True
    dispatched = scheduler.reconcile()

    assert [task.task_id for task in dispatched] == [critical.task_id, low.task_id]


def test_complete_task_records_result_and_history():
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)
    record = scheduler.submit_task(command="collect logs", requested_agent=Agent.SPARK)
    assert record.status is TaskStatus.RUNNING

    completed = scheduler.complete_task(record.task_id, result={"ok": True})

    assert completed.status is TaskStatus.COMPLETED
    assert completed.result == {"ok": True}
    assert any(entry.status is TaskStatus.COMPLETED for entry in completed.history)


def test_cancel_task_clears_assignment_and_records_reason():
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)
    running = scheduler.submit_task(command="initial", requested_agent=Agent.SPARK)
    assert running.assigned_agent is Agent.SPARK

    cancelled = scheduler.cancel_task(running.task_id, reason="operator request")

    assert cancelled.status is TaskStatus.CANCELLED
    assert cancelled.assigned_agent is None
    assert cancelled.error == "operator request"
    assert any(entry.status is TaskStatus.CANCELLED for entry in cancelled.history)


def test_list_tasks_supports_status_filters():
    state = {"healthy": False}

    def provider() -> ResourceSnapshot:
        return _healthy_snapshot() if state["healthy"] else _overloaded_snapshot()

    scheduler = TaskScheduler(health_provider=provider)
    pending = scheduler.submit_task(command="blocked")
    state["healthy"] = True
    running = scheduler.submit_task(command="active")

    assert scheduler.list_tasks(statuses=[TaskStatus.PENDING]) == [pending]
    assert scheduler.list_tasks(statuses=[TaskStatus.RUNNING]) == [running]


def test_missing_task_raises_key_error():
    scheduler = TaskScheduler(health_provider=_healthy_snapshot)

    try:
        scheduler.get_task("missing")
    except KeyError as exc:
        assert "Unknown task_id" in str(exc)
    else:
        raise AssertionError("get_task should reject unknown task IDs")
