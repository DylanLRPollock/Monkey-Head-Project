# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Cli module (src/huey)

"""Top-level command line interface for HueyOS."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Sequence

__all__ = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="huey",
        description="Command line interface for HueyOS runtime and utilities.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    init_cmd = sub.add_parser(
        "init",
        help="Initialise the HueyOS workspace and memory directories.",
    )
    init_cmd.add_argument(
        "--verbose",
        action="store_true",
        help="Print the directories that were created during initialisation.",
    )
    init_cmd.add_argument(
        "--run-checks",
        action="store_true",
        help="Run system compatibility checks after creating directories.",
    )
    init_cmd.set_defaults(handler=_cmd_init)

    run_cmd = sub.add_parser("run", help="Launch the HueyOS runtime.")
    run_cmd.add_argument(
        "--cli",
        action="store_true",
        help="Launch the command line interface instead of the GUI.",
    )
    run_cmd.add_argument(
        "--gui",
        action="store_true",
        help="Explicitly launch the GUI even if other flags request CLI mode.",
    )
    run_cmd.add_argument(
        "--minimal",
        action="store_true",
        help="Use the lightweight CustomPyGPT CLI without GUI dependencies.",
    )
    run_cmd.add_argument(
        "--manager-ui",
        action="store_true",
        help="Launch the Tkinter program manager UI instead of the main runtime.",
    )
    run_cmd.add_argument(
        "--ml",
        action="store_true",
        help="Enable the ML optional dependency profile before launching.",
    )
    run_cmd.add_argument(
        "--cloud",
        action="store_true",
        help="Enable the cloud optional dependency profile before launching.",
    )
    run_cmd.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Additional runtime profiles to export via HUEY_PROFILES.",
    )
    run_cmd.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip operating system and Python compatibility checks.",
    )
    run_cmd.add_argument(
        "--no-fallback",
        action="store_true",
        help="Do not fall back to the CLI if the GUI fails to launch.",
    )
    run_cmd.set_defaults(handler=_cmd_run)

    sys_cmd = sub.add_parser(
        "system-check", help="Run environment diagnostics and compatibility checks."
    )
    sys_cmd.add_argument(
        "--json",
        action="store_true",
        help="Emit the collected results as JSON.",
    )
    sys_cmd.add_argument(
        "--verbose",
        action="store_true",
        help="Always print each individual check result.",
    )
    sys_cmd.set_defaults(handler=_cmd_system_check)

    deploy_cmd = sub.add_parser(
        "deploy", help="Deploy HueyOS services using Docker and/or Kubernetes."
    )
    deploy_cmd.add_argument(
        "--mode",
        choices=["docker", "kubernetes", "all"],
        default="all",
        help="Select which deployment targets to execute.",
    )
    deploy_cmd.add_argument(
        "--compose-file",
        default="docker-compose.yml",
        help="Path to the Docker Compose file to apply.",
    )
    deploy_cmd.add_argument(
        "--manifest",
        default="k8s.yaml",
        help="Path to the Kubernetes manifest to apply.",
    )
    deploy_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them.",
    )
    deploy_cmd.add_argument(
        "--verbose",
        action="store_true",
        help="Show command output even when commands succeed.",
    )
    deploy_cmd.set_defaults(handler=_cmd_deploy)

    agent_cmd = sub.add_parser(
        "agent-status",
        help="Report scheduler task counts and recent resource observations.",
    )
    agent_cmd.add_argument(
        "--json",
        action="store_true",
        help="Emit the status payload as JSON.",
    )
    agent_cmd.add_argument(
        "--verbose",
        action="store_true",
        help="Include details for each tracked task in the output.",
    )
    agent_cmd.set_defaults(handler=_cmd_agent_status)

    sort_cmd = sub.add_parser(
        "memory-sort", help="Organise the shared memory directory by file type."
    )
    sort_cmd.add_argument(
        "--source",
        help="Source directory containing unsorted files (defaults to memory/RAW).",
    )
    sort_cmd.add_argument(
        "--destination",
        help="Destination root directory (defaults to the configured memory path).",
    )
    sort_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned moves without modifying the filesystem.",
    )
    sort_cmd.add_argument(
        "--json",
        action="store_true",
        help="Emit the summary as JSON.",
    )
    sort_cmd.set_defaults(handler=_cmd_memory_sort)

    return parser


def _cmd_init(args: argparse.Namespace) -> int:
    from hueyos.utils.auto_sort import get_extension_map
    from hueyos.utils.paths import ensure_subdirectory, get_memory_path

    memory_path = get_memory_path(create=True)
    created: List[str] = []

    # Always ensure RAW and LOGS directories exist.
    for part in ("RAW", "LOGS"):
        path = ensure_subdirectory(part)
        created.append(str(path))

    categories = sorted({category for category in get_extension_map().values()})
    for category in categories:
        path = ensure_subdirectory(category)
        created.append(str(path))

    unique_created = list(dict.fromkeys(created))
    print(f"Memory initialised at {memory_path}")
    if args.verbose:
        for item in unique_created:
            print(f"  - {item}")

    if args.run_checks:
        from hueyos.system_checks import system_check

        results = system_check()
        print("System check results:")
        for key, value in sorted(results.items()):
            status = "OK" if value else "WARN"
            print(f"  {key}: {status}")

    return 0


def _normalise_profiles(profiles: Iterable[str]) -> List[str]:
    seen: Dict[str, None] = {}
    for profile in profiles:
        name = profile.strip()
        if not name:
            continue
        if name not in seen:
            seen[name] = None
    return list(seen.keys())


def _cmd_run(args: argparse.Namespace) -> int:
    runtime = None
    attempted = ("run", "hueyos.run", "huey.memory.PY.run")
    for module_name in attempted:
        try:
            runtime = import_module(module_name)
        except ModuleNotFoundError:
            continue
        else:
            break
    if runtime is None:
        raise RuntimeError(
            "Unable to locate runtime module (tried run, hueyos.run, "
            "huey.memory.PY.run)."
        )

    requested_profiles: List[str] = []
    if args.ml:
        requested_profiles.append("ml")
    if args.cloud:
        requested_profiles.append("cloud")
    for value in args.profile:
        requested_profiles.extend(part.strip() for part in value.split(","))

    existing = os.environ.get("HUEY_PROFILES", "")
    if existing:
        requested_profiles.extend(part.strip() for part in existing.split(","))

    profiles = _normalise_profiles(requested_profiles)
    if profiles:
        os.environ["HUEY_PROFILES"] = ",".join(profiles)

    if not args.skip_checks:
        from hueyos.core.system_checks import (
            check_os_support,
            check_python_version,
        )

        check_os_support()
        check_python_version()

    launch_gui = getattr(runtime, "launch_gui", None)
    launch_manager_ui = getattr(runtime, "launch_manager_ui", None)
    load_cli = getattr(runtime, "_load_cli", None)
    minimal_run = getattr(runtime, "minimal_run", None)

    try:
        if args.manager_ui:
            if launch_manager_ui is None:
                raise RuntimeError("Manager UI is not available in this runtime build.")
            launch_manager_ui()
            return 0

        if args.minimal:
            if minimal_run is None:
                raise RuntimeError("Minimal CLI mode is not available.")
            minimal_run()
            return 0

        cli_requested = args.cli and not args.gui
        if cli_requested:
            if load_cli is None:
                raise RuntimeError(
                    "CLI launcher is not available in this runtime build."
                )
            runner = load_cli()
            runner()
            return 0

        if launch_gui is None:
            if args.no_fallback:
                raise RuntimeError(
                    "GUI launcher is not available in this runtime build."
                )
            if load_cli is None:
                raise RuntimeError("Neither GUI nor CLI entry points are available.")
            runner = load_cli()
            runner()
            return 0

        try:
            launch_gui()
            return 0
        except Exception:
            if args.no_fallback:
                raise
            print("GUI launch failed; falling back to CLI mode.")
            if load_cli is None:
                raise RuntimeError("GUI launch failed and CLI entry point is missing.")
            runner = load_cli()
            runner()
            return 0
    except KeyboardInterrupt:  # pragma: no cover - interactive usage
        return 130


def _cmd_system_check(args: argparse.Namespace) -> int:
    from hueyos.system_checks import system_check

    results = system_check()
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        if args.verbose:
            print("System check results:")
        for key, value in sorted(results.items()):
            status = "OK" if value else "WARN"
            if args.verbose:
                print(f"  {key}: {status}")
            else:
                print(f"{key}: {status}")
    return 0


def _run_command(
    command: Sequence[str], *, dry_run: bool, verbose: bool
) -> subprocess.CompletedProcess[str] | None:
    if dry_run:
        print(f"[dry-run] {' '.join(command)}")
        return None

    try:
        result = subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=not verbose,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Command not found: {command[0]}") from exc

    if verbose:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    else:
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"Command {' '.join(command)} exited with {result.returncode}"
        )
    return result


def _cmd_deploy(args: argparse.Namespace) -> int:
    tasks: List[tuple[str, Sequence[str]]] = []

    if args.mode in ("docker", "all"):
        compose_path = Path(args.compose_file).expanduser().resolve()
        if not compose_path.exists():
            raise RuntimeError(f"Docker compose file not found: {compose_path}")
        tasks.append(
            (
                "docker",
                [
                    "docker",
                    "compose",
                    "-f",
                    str(compose_path),
                    "up",
                    "-d",
                ],
            )
        )

    if args.mode in ("kubernetes", "all"):
        manifest_path = Path(args.manifest).expanduser().resolve()
        if not manifest_path.exists():
            raise RuntimeError(f"Kubernetes manifest not found: {manifest_path}")
        tasks.append(("kubectl", ["kubectl", "apply", "-f", str(manifest_path)]))

    for label, command in tasks:
        if label == "docker" and shutil.which("docker") is None:
            raise RuntimeError("Docker executable not found on PATH.")
        if label == "kubectl" and shutil.which("kubectl") is None:
            raise RuntimeError("kubectl executable not found on PATH.")
        _run_command(command, dry_run=args.dry_run, verbose=args.verbose)

    if not tasks:
        print("No deployment tasks selected.")
    return 0


def _cmd_agent_status(args: argparse.Namespace) -> int:
    from huey.api import SCHEDULER
    from hueyos.core.task_scheduler import Agent, TaskStatus

    records = SCHEDULER.list_tasks()
    status_counts: Dict[str, int] = {status.value: 0 for status in TaskStatus}
    agent_counts: Dict[str, int] = {agent.value: 0 for agent in Agent}

    for record in records:
        status_counts[record.status.value] = (
            status_counts.get(record.status.value, 0) + 1
        )
        if record.assigned_agent:
            agent_counts[record.assigned_agent.value] = (
                agent_counts.get(record.assigned_agent.value, 0) + 1
            )

    snapshot = SCHEDULER.health_provider()
    snapshot_payload = {
        "timestamp": getattr(snapshot, "timestamp", None),
        "cpu_percent": getattr(snapshot, "cpu_percent", None),
        "memory_available": getattr(snapshot, "memory_available", None),
        "memory_total": getattr(snapshot, "memory_total", None),
        "battery_percent": getattr(snapshot, "battery_percent", None),
        "notes": getattr(snapshot, "notes", None),
    }

    payload: Dict[str, Any] = {
        "total_tasks": len(records),
        "tasks_by_status": {k: v for k, v in sorted(status_counts.items())},
        "tasks_by_agent": {k: v for k, v in sorted(agent_counts.items())},
        "resource_snapshot": snapshot_payload,
    }

    if args.verbose:
        payload["tasks"] = [record.to_dict() for record in records]

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Total tasks: {payload['total_tasks']}")
        for status, count in payload["tasks_by_status"].items():
            print(f"  {status}: {count}")
        for agent, count in payload["tasks_by_agent"].items():
            print(f"  agent {agent}: {count}")
        notes = snapshot_payload.get("notes")
        cpu = snapshot_payload.get("cpu_percent")
        mem_avail = snapshot_payload.get("memory_available")
        mem_total = snapshot_payload.get("memory_total")
        if cpu is not None:
            print(f"  cpu_percent: {cpu}")
        if mem_avail is not None and mem_total is not None and mem_total:
            percent_free = (mem_avail / mem_total) * 100
            print(f"  memory_free: {percent_free:.1f}%")
        if notes:
            print(f"  notes: {notes}")
    return 0


def _cmd_memory_sort(args: argparse.Namespace) -> int:
    from hueyos.utils.auto_sort import auto_sort_memory

    try:
        summary = auto_sort_memory(
            source_dir=args.source,
            destination_root=args.destination,
            dry_run=args.dry_run,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(str(exc)) from exc
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Source: {summary['source']}")
        print(f"Destination: {summary['destination']}")
        print(f"Moved {len(summary['moved'])} file(s)")
        if summary["skipped"]:
            print(f"Skipped {len(summary['skipped'])} file(s):")
            for item in summary["skipped"]:
                print(f"  - {item}")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler: Callable[[argparse.Namespace], int] = getattr(args, "handler")
    try:
        return handler(args)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover - manual CLI usage
    sys.exit(main())
