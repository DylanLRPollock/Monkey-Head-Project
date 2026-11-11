"""Cover task scheduler serialization and less common lifecycle paths."""

from __future__ import annotations

from huey.core.task_scheduler import (
    Agent,
    ResourceProfile,
    ResourceSnapshot,
    TaskPriority,
    TaskScheduler,
    TaskStatus,
)


def test_task_record_serializes_populated_and_empty_optional_fields():
    scheduler = TaskScheduler(
        health_provider=lambda: ResourceSnapshot(
            timestamp=12.5,
            cpu_percent=10.0,
            memory_available=8.0,
            memory_total=10.0,
            battery_percent=75.0,
            notes="healthy",
        )
    )
    running = scheduler.submit_task(
        command="run",
        priority=TaskPriority.HIGH,
        requested_agent=Agent.SPARK,
        metadata={"source": "test"},
        resource_profile=ResourceProfile(cpu=0.4, memory=0.3, battery=0.2, gpu=0.1),
        owner_subject="operator-1",
    )
    running_dict = running.to_dict()

    assert running_dict["owner_subject"] == "operator-1"
    assert running_dict["requested_agent"] == "spark"
    assert running_dict["assigned_agent"] == "spark"
    assert running_dict["priority"] == int(TaskPriority.HIGH)
    assert running_dict["resource_profile"] == {
        "cpu": 0.4,
        "memory": 0.3,
        "battery": 0.2,
        "gpu": 0.1,
    }
    assert running_dict["snapshot"] == {
        "timestamp": 12.5,
        "cpu_percent": 10.0,
        "memory_available": 8.0,
        "memory_total": 10.0,
        "battery_percent": 75.0,
        "notes": "healthy",
    }
    assert running_dict["history"][0]["status"] == "running"

    pending = TaskScheduler(
        health_provider=lambda: ResourceSnapshot(cpu_percent=100.0)
    ).submit_task(command="wait")
    pending_dict = pending.to_dict()
    assert pending_dict["requested_agent"] is None
    assert pending_dict["assigned_agent"] is None
    assert pending_dict["snapshot"]["memory_available"] is None


def test_resource_checks_cover_memory_and_battery_thresholds():
    memory_limited = TaskScheduler(
        health_provider=lambda: ResourceSnapshot(
            cpu_percent=None, memory_available=1.0, memory_total=10.0
        )
    ).submit_task(command="memory constrained")
    assert memory_limited.status is TaskStatus.PENDING
    assert "Insufficient memory headroom" in memory_limited.history[-1].message

    battery_limited = TaskScheduler(
        health_provider=lambda: ResourceSnapshot(
            cpu_percent=None, memory_available=None, battery_percent=20.0
        )
    ).submit_task(command="battery constrained")
    assert battery_limited.status is TaskStatus.PENDING
    assert "Battery level 20% below threshold" in battery_limited.history[-1].message

    at_threshold = TaskScheduler(
        cpu_threshold=85.0,
        health_provider=lambda: ResourceSnapshot(cpu_percent=80.5),
    ).submit_task(command="threshold boundary")
    assert at_threshold.status is TaskStatus.RUNNING


def test_reconcile_skips_running_tasks_and_keeps_blocked_work_pending():
    healthy = TaskScheduler(health_provider=lambda: ResourceSnapshot())
    active = healthy.submit_task(command="already running")
    assert healthy.reconcile() == []
    assert active.status is TaskStatus.RUNNING

    blocked = TaskScheduler(health_provider=lambda: ResourceSnapshot(cpu_percent=100.0))
    waiting = blocked.submit_task(command="still blocked")
    assert blocked.reconcile() == []
    assert waiting.status is TaskStatus.PENDING
    assert waiting.history[-1].message.startswith("CPU utilisation")


def test_failure_exhaustion_and_health_blocked_retry_end_in_failed_state():
    exhausted = TaskScheduler(max_retries=0, health_provider=lambda: ResourceSnapshot())
    first = exhausted.submit_task(command="no retries")
    failed = exhausted.fail_task(first.task_id, "permanent failure")
    assert failed.status is TaskStatus.FAILED
    assert failed.assigned_agent is None
    assert failed.error == "permanent failure"

    state = {"healthy": True}
    blocked = TaskScheduler(
        health_provider=lambda: ResourceSnapshot(
            cpu_percent=10.0 if state["healthy"] else 100.0
        )
    )
    second = blocked.submit_task(command="retry blocked")
    state["healthy"] = False
    failed_retry = blocked.fail_task(second.task_id, "worker stopped")
    assert failed_retry.status is TaskStatus.FAILED
    assert failed_retry.history[-2].message.startswith("CPU utilisation")


def test_cancel_pending_and_terminal_tasks_is_safe():
    scheduler = TaskScheduler(
        health_provider=lambda: ResourceSnapshot(cpu_percent=100.0)
    )
    pending = scheduler.submit_task(command="waiting")
    cancelled = scheduler.cancel_task(pending.task_id)
    assert cancelled.status is TaskStatus.CANCELLED
    assert cancelled.assigned_agent is None

    healthy = TaskScheduler(health_provider=lambda: ResourceSnapshot())
    active = healthy.submit_task(command="complete first")
    completed = healthy.complete_task(active.task_id)
    assert healthy.cancel_task(active.task_id) is completed
    assert completed.status is TaskStatus.COMPLETED
    assert healthy.cancel_task(active.task_id).status is TaskStatus.COMPLETED


def test_pending_task_failure_completion_and_unfiltered_listing():
    state = {"healthy": False}
    scheduler = TaskScheduler(
        health_provider=lambda: ResourceSnapshot(
            cpu_percent=10.0 if state["healthy"] else 100.0
        )
    )
    pending = scheduler.submit_task(command="pending without an agent")
    assert pending.assigned_agent is None

    state["healthy"] = True
    retried = scheduler.fail_task(pending.task_id, "initial dispatch failed")
    assert retried.status is TaskStatus.RUNNING
    assert retried.assigned_agent is Agent.SPARK
    assert retried.attempts == 1

    scheduler.complete_task(retried.task_id)
    assert scheduler.list_tasks() == [retried]

    state["healthy"] = False
    never_assigned = scheduler.submit_task(command="also pending")
    completed = scheduler.complete_task(never_assigned.task_id)
    assert completed.status is TaskStatus.COMPLETED
