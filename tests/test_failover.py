# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Failover module (tests)

from pathlib import Path

from hueyos.scripts.failover import (
    build_failover_plan,
    execute_plan,
    simulate_hot_swap,
)


def test_build_failover_plan_constructs_commands():
    plan = build_failover_plan(
        Path("/primary"),
        Path("/secondary"),
        volumes=["etc"],
        excludes=["tmp"],
        dry_run=True,
    )
    assert plan.tasks
    command = plan.tasks[0].command
    assert command[0] == "rsync"
    assert "--dry-run" in command
    assert any(entry.startswith("--exclude=tmp") for entry in command)


def test_execute_plan_invokes_runner(monkeypatch):
    plan = build_failover_plan(Path("/a"), Path("/b"), volumes=["home"], excludes=[])
    executed = []

    def runner(cmd):
        executed.append(cmd)

    execute_plan(plan, runner=runner)
    assert executed == plan.commands()


def test_simulate_hot_swap_runs_verification(monkeypatch):
    plan = build_failover_plan(Path("/a"), Path("/b"), volumes=["etc"], excludes=[])
    called = []

    def runner(cmd):
        called.append(cmd)

    monkeypatch.setattr("hueyos.scripts.failover.time.sleep", lambda _: None)
    simulate_hot_swap(plan, runner=runner)
    assert called
