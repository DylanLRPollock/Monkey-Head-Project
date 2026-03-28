"""Simple failover planning helpers.

The utilities here provide minimal structures for building and executing
synchronisation plans between a primary and secondary filesystem. They are
lightweight by design and focused on the unit-test scenarios in this kata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List
import time


@dataclass
class Task:
    """Represents a single shell command to execute."""

    command: List[str]


@dataclass
class FailoverPlan:
    """Collection of tasks to mirror volumes to a secondary target."""

    source: Path
    target: Path
    volumes: list[str]
    excludes: list[str]
    dry_run: bool = False
    tasks: List[Task] = field(default_factory=list)

    def commands(self) -> List[List[str]]:
        """Return a list of commands for execution."""

        return [task.command for task in self.tasks]


def _build_rsync_command(source: Path, target: Path, volume: str, excludes: Iterable[str], dry_run: bool) -> List[str]:
    command = ["rsync", "-a", "--delete"]
    if dry_run:
        command.append("--dry-run")
    command.extend([f"--exclude={pattern}" for pattern in excludes])
    command.append(f"{source / volume}/")
    command.append(str(target / volume))
    return command


def build_failover_plan(source: Path, target: Path, *, volumes: list[str], excludes: list[str], dry_run: bool = False) -> FailoverPlan:
    """Create a failover plan containing rsync commands for each volume."""

    plan = FailoverPlan(source=source, target=target, volumes=list(volumes), excludes=list(excludes), dry_run=dry_run)
    plan.tasks = [
        Task(command=_build_rsync_command(source, target, volume, excludes, dry_run))
        for volume in plan.volumes
    ]
    return plan


def execute_plan(plan: FailoverPlan, *, runner: Callable[[List[str]], None] | None = None) -> None:
    """Execute each command in the plan using the provided runner."""

    if runner is None:
        import subprocess

        def runner(cmd: List[str]) -> None:  # type: ignore[redefinition]
            subprocess.run(cmd, check=False)

    for command in plan.commands():
        runner(command)


def simulate_hot_swap(plan: FailoverPlan, *, runner: Callable[[List[str]], None] | None = None) -> None:
    """Simulate a hot-swap by executing tasks then verifying synchronisation."""

    execute_plan(plan, runner=runner)
    time.sleep(1)
    if runner is not None:
        for command in plan.commands():
            runner(command)


__all__ = [
    "Task",
    "FailoverPlan",
    "build_failover_plan",
    "execute_plan",
    "simulate_hot_swap",
]
