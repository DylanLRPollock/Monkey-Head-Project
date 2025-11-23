# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Failover module (huey/scripts)

"""Dual-motherboard failover orchestration utilities.

The HueyOS hardware topology includes redundant motherboards. This module
produces repeatable replication plans that can be executed manually or by
a CI pipeline to mirror the active system onto the standby board.
"""

from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List, Sequence

LOGGER = logging.getLogger(__name__)

CommandRunner = Callable[[Sequence[str]], None]


@dataclass
class ReplicationTask:
    """Represents a single rsync style replication command."""

    source: Path
    target: Path
    command: List[str]


@dataclass
class FailoverPlan:
    """Describes the work required to mirror the primary system."""

    primary_root: Path
    secondary_root: Path
    tasks: List[ReplicationTask] = field(default_factory=list)
    hot_swap_delay: float = 5.0
    created_at: float = field(default_factory=lambda: time.time())

    def commands(self) -> List[List[str]]:
        return [task.command for task in self.tasks]


def build_failover_plan(
    primary_root: Path,
    secondary_root: Path,
    *,
    volumes: Iterable[str] | None = None,
    excludes: Iterable[str] | None = None,
    dry_run: bool = False,
) -> FailoverPlan:
    """Create a failover plan that mirrors key volumes to the standby board."""

    volumes = list(volumes or ("etc", "var", "home", "opt"))
    excludes = list(excludes or ("/proc", "/sys", "/dev"))

    plan = FailoverPlan(primary_root=primary_root, secondary_root=secondary_root)
    for volume in volumes:
        source = primary_root / volume
        target = secondary_root / volume
        command = [
            "rsync",
            "-aH",
            "--delete",
            "--numeric-ids",
            str(source) + "/",
            str(target),
        ]
        for pattern in excludes:
            command.insert(3, f"--exclude={pattern}")
        if dry_run:
            command.insert(1, "--dry-run")
        plan.tasks.append(
            ReplicationTask(source=source, target=target, command=command)
        )
        LOGGER.debug("Planned replication of %s -> %s", source, target)
    return plan


def execute_plan(plan: FailoverPlan, runner: CommandRunner | None = None) -> None:
    """Execute the replication commands for the supplied plan."""

    runner = runner or (lambda cmd: subprocess.run(cmd, check=True))
    for task in plan.tasks:
        LOGGER.info("Replicating %s -> %s", task.source, task.target)
        runner(task.command)


def simulate_hot_swap(plan: FailoverPlan, runner: CommandRunner | None = None) -> None:
    """Simulate a hot swap by running a basic verification command set."""

    runner = runner or (lambda cmd: subprocess.run(cmd, check=True))
    verification_commands = [
        ["test", "-d", str(plan.secondary_root / "etc")],
        ["test", "-d", str(plan.secondary_root / "var")],
    ]
    for command in verification_commands:
        LOGGER.debug("Verifying failover target: %s", " ".join(command))
        runner(command)
    LOGGER.info(
        "Hot swap simulation waiting %.1f seconds before declaring success",
        plan.hot_swap_delay,
    )
    time.sleep(plan.hot_swap_delay)
