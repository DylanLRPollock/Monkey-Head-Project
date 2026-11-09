# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Run module (huey)

"""Runtime entry points integrating the PyHuey stack with Monkey Head."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from huey.os.core.privileged_operations import authorize_privileged_operation

from .function_registry import describe_functions, invoke_function
from .pygpt_integration import prepare_pygpt, pyhuey_status

SYSTEM_DIAGNOSTIC_COMMANDS = {
    "date": ["date", "-u"],
    "df": ["df", "-h"],
    "free": ["free", "-h"],
    "uname": ["uname", "-a"],
    "uptime": ["uptime"],
    "whoami": ["whoami"],
}


def minimal_run() -> None:
    """Run the explicitly requested echo-only demonstration CLI."""

    os.environ["MONKEY_HEAD_LIGHT_IMPORTS"] = "1"
    from .pygpt_custom_cli import CustomPyGPT

    CustomPyGPT().run_cli()


def run_sys_code(
    cmd: str,
    *,
    confirmed: bool = False,
    actor_role: str | None = None,
    dry_run: bool = False,
) -> bool:
    """Run one allowlisted diagnostic after explicit admin authorization."""

    authorized = authorize_privileged_operation(
        "host.execute_command",
        confirmed=confirmed,
        actor_role=actor_role,
        dry_run=dry_run,
    )
    if not authorized:
        return False

    if not isinstance(cmd, str):
        raise ValueError("Diagnostic command must be a string alias")
    command = SYSTEM_DIAGNOSTIC_COMMANDS.get(cmd.strip().lower())
    if command is None:
        raise ValueError(
            "Unsupported diagnostic command; choose one of: "
            + ", ".join(sorted(SYSTEM_DIAGNOSTIC_COMMANDS))
        )
    result = subprocess.run(
        command,
        capture_output=True,
        shell=False,
        timeout=300,
    )
    if result.stdout:
        print(result.stdout.decode(), end="")
    if result.stderr:
        print(result.stderr.decode(), end="", file=sys.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}")
    return True


def _run_container_option(args: argparse.Namespace) -> bool:
    """Dispatch the explicitly requested project container operation."""
    if not (args.docker_compose or args.kubernetes):
        return False
    try:
        from .services import container_management
    except ImportError:  # pragma: no cover - fallback to legacy package
        from huey.memory.PY import container_management  # type: ignore

    operation = (
        container_management.manage_containers
        if args.docker_compose
        else container_management.deploy_kubernetes
    )
    operation(
        confirmed=args.yes,
        actor_role="operator" if args.yes else None,
        dry_run=args.dry_run,
    )
    return True


def run_module(target: str) -> None:
    """Import ``module[:func]`` and call the resulting callable."""

    module_name, _, func_name = target.partition(":")
    if not func_name:
        func_name = "main"
    module = importlib.import_module(module_name)
    try:
        func = getattr(module, func_name)
    except AttributeError as exc:  # pragma: no cover - invalid func
        raise ImportError(f"Function {func_name} not found in {module_name}") from exc
    func()


def _prepare_pygpt(source: str | None = None) -> bool:
    """Prepare the explicitly selected legacy test stub, if requested."""

    return prepare_pygpt(source=source)


def _load_cli(source: str | None = None) -> Callable[..., None]:
    """Fail explicitly rather than substitute the echo demo for PyGPT."""
    raise RuntimeError(
        "The legacy PyGPT CLI is retired. Use 'huey-pygpt gui' for upstream "
        "PyGPT or '--minimal' for the echo-only demo."
    )


def launch_cli(*args, source: str | None = None, **kwargs) -> None:
    """Launch the PyHuey CLI entry point if available."""

    cli_run = _load_cli(source)
    cli_run(*args, **kwargs)


def launch_gui(source: str | None = None) -> None:
    """Launch the separate upstream GUI through the canonical launcher."""
    from huey.integrations.pygpt_cli import launch_gui as launch_upstream

    workdir = os.environ.get("PYGPT_WORKDIR")
    result = launch_upstream(workdir=Path(workdir) if workdir else None)
    if result:
        raise RuntimeError(f"PyGPT GUI exited with status {result}; see stderr.")


def list_custom_functions(source: str | None = None) -> list[dict[str, object]]:
    """Return metadata for custom functions exposed through the PyHuey bridge."""

    _prepare_pygpt(source)
    return describe_functions()


def print_custom_functions(source: str | None = None) -> None:
    """Print the registered custom functions available to PyHuey."""

    functions = list_custom_functions(source)
    if not functions:
        print("No custom functions registered.")
        return

    print("Custom functions")
    for function in functions:
        print(f"  - {function['name']}{function['signature']} :: {function['module']}")


def _parse_custom_function_kwargs(raw: str | None) -> dict[str, object]:
    if raw in {None, "", "{}"}:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Custom function kwargs must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Custom function kwargs must decode to a JSON object")
    return payload


def run_custom_function(
    function_name: str,
    kwargs_json: str | None = None,
    *,
    source: str | None = None,
) -> object:
    """Run a registered custom function and return its result."""

    _prepare_pygpt(source)
    return invoke_function(function_name, **_parse_custom_function_kwargs(kwargs_json))


def print_pyhuey_info(source: str | None = None) -> None:
    """Print a concise PyHuey integration report."""

    status = pyhuey_status(source=source)
    active = status["active_source"]

    print("PyHuey integration")
    print(f"  prepared: {status['prepared']}")
    print(f"  version: {status['version'] or 'unknown'}")
    print(f"  module: {status['module_file'] or 'unresolved'}")
    if isinstance(active, dict):
        print(f"  source: {active['name']} ({active['kind']})")
        print(f"  source path: {active['path']}")
    else:
        print(f"  source: {active}")

    print("  candidates:")
    for candidate in status["candidates"]:
        marker = "yes" if candidate["exists"] else "no"
        print(f"    - {candidate['name']}: {marker} :: {candidate['path']}")
    print(f"  custom functions: {status['custom_function_count']}")
    for function in status["custom_functions"]:
        print(f"    - {function['name']}{function['signature']}")


def launch_manager_ui() -> None:
    """Start the Tkinter-based program manager shipped with Monkey Head."""

    try:
        import tkinter as tk
    except Exception as exc:  # pragma: no cover - missing tkinter
        raise RuntimeError("tkinter is not available") from exc

    from .main_ui import MainUI

    root = tk.Tk()
    MainUI(root)
    root.mainloop()


def launch_install_gui() -> None:
    """Start the graphical installer flow with required license confirmation."""

    from huey.install_gui import launch_install_gui as start_install_gui

    start_install_gui()


def main(argv: list[str] | None = None) -> None:
    """Entry point used by the ``run`` wrapper script."""

    parser = argparse.ArgumentParser(description="Launch the Monkey Head Project")
    parser.add_argument("--cli", action="store_true", help="Run CLI instead of GUI")
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Run the echo-only CustomPyGPT test/demo CLI (not PyGPT)",
    )
    parser.add_argument(
        "--simple-chat",
        action="store_true",
        help="Run simple chat demonstration GUI",
    )
    parser.add_argument(
        "--module",
        type=str,
        help="Run specified module optionally with :func",
    )
    parser.add_argument(
        "--version", action="store_true", help="Report PyGPT launcher status and exit"
    )
    parser.add_argument(
        "--pyhuey-info",
        action="store_true",
        help="Print PyHuey integration discovery status and exit",
    )
    parser.add_argument(
        "--pyhuey-source",
        choices=("auto", "package"),
        default="auto",
        help="Select deprecated test-stub compatibility for legacy diagnostics",
    )
    parser.add_argument(
        "--list-custom-functions",
        action="store_true",
        help="List custom functions available through the PyHuey integration",
    )
    parser.add_argument(
        "--run-custom-function",
        type=str,
        metavar="NAME",
        help="Run a registered custom function and print its JSON result",
    )
    parser.add_argument(
        "--custom-function-kwargs",
        type=str,
        default="{}",
        metavar="JSON",
        help="JSON object of keyword arguments for --run-custom-function",
    )
    parser.add_argument(
        "--list-pdfs", action="store_true", help="List PDF files available to the app"
    )
    parser.add_argument(
        "--system-check",
        action="store_true",
        help="Run environment checks and exit",
    )
    parser.add_argument(
        "--docker-compose",
        action="store_true",
        help="Build image and start Docker Compose stack",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Explicitly authorize the requested command or container operation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview a container or cluster operation without running commands",
    )
    parser.add_argument(
        "--kubernetes",
        action="store_true",
        help="Deploy resources using manifests in k8s/",
    )
    parser.add_argument(
        "--manager-ui",
        action="store_true",
        help="Launch the Tkinter program manager",
    )
    parser.add_argument(
        "--install-gui",
        action="store_true",
        help="Launch the graphical installer (requires license acceptance)",
    )
    parser.add_argument(
        "--sys-code",
        type=str,
        metavar="DIAGNOSTIC",
        help="Run an allowlisted diagnostic (date, df, free, uname, uptime, whoami)",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to main.config for logging",
    )
    parser.add_argument(
        "--workdir",
        type=str,
        help="Set the working directory (default: project directory)",
    )
    args = parser.parse_args(argv)

    if args.config:
        os.environ["MONKEY_HEAD_CONFIG"] = os.path.abspath(args.config)

    if args.workdir:
        os.environ["PYGPT_WORKDIR"] = os.path.abspath(args.workdir)

    if args.module:
        run_module(args.module)
        return

    if args.minimal:
        minimal_run()
        return

    if args.sys_code:
        run_sys_code(
            args.sys_code,
            confirmed=args.yes,
            actor_role="admin" if args.yes else None,
            dry_run=args.dry_run,
        )
        return

    if args.list_pdfs:
        from .pdf_utils import list_available_pdfs

        for path in list_available_pdfs():
            print(path)
        return

    if args.system_check:
        from .system_checks import system_check

        system_check()
        return

    if _run_container_option(args):
        return

    if args.manager_ui:
        launch_manager_ui()
        return

    if args.install_gui:
        launch_install_gui()
        return

    if args.pyhuey_info:
        print_pyhuey_info(args.pyhuey_source)
        return

    if args.list_custom_functions:
        print_custom_functions(args.pyhuey_source)
        return

    if args.run_custom_function:
        result = run_custom_function(
            args.run_custom_function,
            args.custom_function_kwargs,
            source=args.pyhuey_source,
        )
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return

    if args.version:
        from huey.integrations.pygpt_cli import doctor

        print(json.dumps(doctor(), indent=2))
        return

    from .system_checks import check_os_support, check_python_version

    check_os_support()
    check_python_version()

    if args.cli:
        launch_cli(source=args.pyhuey_source)
        return

    if args.simple_chat:
        try:
            from .legacy.simple_chat import main as simple_chat_main
        except ImportError as exc:  # pragma: no cover - optional legacy feature
            raise RuntimeError("Simple chat UI is not available") from exc

        simple_chat_main()
        return

    launch_gui(args.pyhuey_source)


__all__ = [
    "_load_cli",
    "launch_cli",
    "launch_gui",
    "launch_install_gui",
    "launch_manager_ui",
    "list_custom_functions",
    "main",
    "minimal_run",
    "print_custom_functions",
    "print_pyhuey_info",
    "run_custom_function",
    "run_module",
    "run_sys_code",
]
