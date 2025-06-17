#!/usr/bin/env python3
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2023.12.05 22:00:00                  #
# ================================================== #

import argparse
import importlib
import os
import sys
from pathlib import Path
import subprocess


def minimal_run() -> None:
    """Run the lightweight CLI without GUI dependencies."""
    os.environ["MONKEY_HEAD_LIGHT_IMPORTS"] = "1"
    from monkey_head.pygpt_custom_cli import CustomPyGPT

    CustomPyGPT().run_cli()


def run_sys_code(cmd: str) -> None:
    """Execute a system command and print output."""
    result = subprocess.run(
        cmd,
        shell=True,
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
    """Import ``module[:func]`` and execute the callable.

    Parameters
    ----------
    target : str
        Module path optionally followed by ``:func``. ``func`` defaults to
        ``"main"`` when omitted.
    """
    module_name, _, func_name = target.partition(":")
    if not func_name:
        func_name = "main"
    mod = importlib.import_module(module_name)
    try:
        func = getattr(mod, func_name)
    except AttributeError as exc:  # pragma: no cover - invalid func
        raise ImportError(f"Function {func_name} not found in {module_name}") from exc
    func()


def _load_cli() -> "callable":
    """Import and return the standard CLI runner.

    Falls back to the ``repo/pygpt-MHP`` submodule if the mirrored ``src``
    directory or installed package is missing.
    """
    src_dir = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_dir.resolve()))
    try:
        from pygpt_net.app import run as cli_run
    except Exception:  # pragma: no cover - fallback to submodule
        sub_dir = Path(__file__).parent / "repo" / "pygpt-MHP" / "src"
        if sub_dir.exists() and str(sub_dir.resolve()) not in sys.path:
            sys.path.insert(0, str(sub_dir.resolve()))
        try:
            from pygpt_net.app import run as cli_run
        except Exception:  # pragma: no cover - missing GUI deps
            return minimal_run

    return cli_run


def launch_gui() -> None:
    """Start the PyGPT GUI with Monkey Head extensions."""
    from pygpt_net.app import run as pygpt_run
    from monkey_head.pygpt_net.tools.manager import MonkeyManager

    pygpt_run(tools=[MonkeyManager()])


def launch_manager_ui() -> None:
    """Start the Tkinter program manager."""
    from gui.main_ui import MainUI
    try:
        import tkinter as tk
    except Exception as exc:  # pragma: no cover - missing tkinter
        raise RuntimeError("tkinter is not available") from exc

    root = tk.Tk()
    MainUI(root)
    root.mainloop()


def main() -> None:
    """Launch the GUI by default with an optional CLI mode."""

    parser = argparse.ArgumentParser(description="Launch the Monkey Head Project")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in command-line mode instead of the GUI",
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Run lightweight CustomPyGPT CLI",
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
        "--version",
        action="store_true",
        help="Print pygpt_net version and exit",
    )
    parser.add_argument(
        "--list-pdfs",
        action="store_true",
        help="List PDF files available to the application",
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
        "--sys-code",
        type=str,
        metavar="CMD",
        help="Execute system command and exit",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to CONFIG.txt for logging",
    )
    parser.add_argument(
        "--workdir",
        type=str,
        help="Set the working directory (default: project directory)",
    )
    args = parser.parse_args()

    if args.config:
        os.environ["MONKEY_HEAD_CONFIG"] = os.path.abspath(args.config)

    # determine working directory
    if args.workdir:
        os.environ["PYGPT_WORKDIR"] = os.path.abspath(args.workdir)
    elif "PYGPT_WORKDIR" not in os.environ:
        os.environ["PYGPT_WORKDIR"] = str(Path(__file__).parent.resolve())

    if args.module:
        run_module(args.module)
        return

    if args.minimal:
        minimal_run()
        return
    if args.simple_chat:
        from monkey_head.simple_chat_gui import run_simple_chat

        run_simple_chat()
        return

    if args.list_pdfs:
        from monkey_head.pdf_utils import list_available_pdfs

        for pdf in list_available_pdfs():
            print(pdf)
        return

    if args.system_check:
        from monkey_head.core.system_checks import system_check

        system_check()
        return

    if args.docker_compose:
        from monkey_head.services.container_management import manage_containers

        manage_containers()
        return

    if args.kubernetes:
        from monkey_head.services.container_management import deploy_kubernetes

        deploy_kubernetes()
        return

    if args.manager_ui:
        launch_manager_ui()
        return
    if args.sys_code:
        run_sys_code(args.sys_code)
        return

    from monkey_head.core.system_checks import check_os_support, check_python_version

    cli_run = _load_cli()

    # Warn if running on an unsupported operating system
    check_os_support()
    # Warn if running an experimental Python version
    check_python_version()

    if args.version:
        from pygpt_net import __version__

        print(f"pygpt_net version: {__version__}")
        return

    if args.cli:
        cli_run()
        return

    try:
        launch_gui()
    except Exception as exc:
        print(f"GUI failed to launch: {exc}\nFalling back to CLI mode.")
        cli_run()


if __name__ == "__main__":
    main()
