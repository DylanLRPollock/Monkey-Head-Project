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
from pathlib import Path
from typing import Callable

from huey.os.core.platform_support import split_command_line

from .function_registry import describe_functions, invoke_function
from .pygpt_integration import prepare_pygpt, pyhuey_status


def minimal_run() -> None:
    """Run the lightweight CLI without importing heavy GUI dependencies."""

    os.environ["MONKEY_HEAD_LIGHT_IMPORTS"] = "1"
    from .pygpt_custom_cli import CustomPyGPT

    CustomPyGPT().run_cli()


def run_sys_code(cmd: str) -> None:
    """Execute ``cmd`` without invoking a shell and stream stdout/stderr."""

    command = split_command_line(cmd)
    if not command:
        raise ValueError("No command provided.")
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.stdout:
        print(result.stdout.decode(), end="")
    if result.stderr:
        print(result.stderr.decode(), end="", file=sys.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}")


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
    """Ensure :mod:`pygpt_net` is importable either from site-packages or vendors."""

    return prepare_pygpt(source=source)


def _load_cli(source: str | None = None) -> Callable[..., None]:
    """Import and return the canonical PyHuey CLI runner.

    Falls back to :func:`minimal_run` if the CLI cannot be imported due to
    missing dependencies.
    """

    if not _prepare_pygpt(source):
        return minimal_run

    try:
        from pygpt_net.app import run as cli_run
    except Exception:  # pragma: no cover - fallback to bundled sources
        return minimal_run
    return cli_run


def launch_cli(*args, source: str | None = None, **kwargs) -> None:
    """Launch the PyHuey CLI entry point if available."""

    cli_run = _load_cli(source)
    cli_run(*args, **kwargs)


def launch_gui(source: str | None = None) -> None:
    """Start the PyHuey GUI with the Monkey Head manager tool enabled."""

    if not _prepare_pygpt(source):
        raise RuntimeError("pygpt_net package is not available")

    from pygpt_net.app import run as pygpt_run

    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    pygpt_run(tools=[MonkeyManager()])


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
        print(
            "  - "
            f"{function['name']}{function['signature']} :: {function['module']}"
        )


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
    return invoke_function(
        function_name, **_parse_custom_function_kwargs(kwargs_json)
    )


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
        help="Run lightweight CustomPyHuey CLI",
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
        "--version", action="store_true", help="Print pygpt_net version and exit"
    )
    parser.add_argument(
        "--pyhuey-info",
        action="store_true",
        help="Print PyHuey integration discovery status and exit",
    )
    parser.add_argument(
        "--pyhuey-source",
        choices=("auto", "installed", "package", "pyhuey", "vendor"),
        default=os.environ.get("PYHUEY_SOURCE", "auto"),
        help="Select PyHuey/PyGPT-net source discovery preference",
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
        metavar="CMD",
        help="Execute system command and exit",
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
    elif "PYGPT_WORKDIR" not in os.environ:
        os.environ["PYGPT_WORKDIR"] = str(Path(__file__).resolve().parent.parent)

    if args.module:
        run_module(args.module)
        return

    if args.minimal:
        minimal_run()
        return

    if args.sys_code:
        run_sys_code(args.sys_code)
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

    if args.docker_compose:
        try:
            from .services import container_management
        except ImportError:  # pragma: no cover - fallback to legacy package
            from huey.memory.PY import container_management  # type: ignore

        container_management.manage_containers()
        return

    if args.kubernetes:
        try:
            from .services import container_management
        except ImportError:  # pragma: no cover - fallback to legacy package
            from huey.memory.PY import container_management  # type: ignore

        container_management.deploy_kubernetes()
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
        _prepare_pygpt(args.pyhuey_source)
        try:
            from pygpt_net import __version__
        except Exception:  # pragma: no cover - pygpt missing
            __version__ = "unknown"
        print(f"pygpt_net version: {__version__}")
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

    try:
        launch_gui(args.pyhuey_source)
    except Exception as exc:  # pragma: no cover - fallback to CLI
        print(f"GUI failed to launch: {exc}\nFalling back to CLI mode.")
        launch_cli(source=args.pyhuey_source)


__all__ = [
    "_load_cli",
    "launch_cli",
    "launch_gui",
    "launch_manager_ui",
    "launch_install_gui",
    "list_custom_functions",
    "print_pyhuey_info",
    "print_custom_functions",
    "main",
    "minimal_run",
    "run_custom_function",
    "run_module",
    "run_sys_code",
]
