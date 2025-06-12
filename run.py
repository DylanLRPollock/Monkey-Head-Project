#!/usr/bin/env python3
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
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
import sys
from pathlib import Path

from monkey_head.core.system_checks import check_os_support

sys.path.insert(0, str((Path(__file__).parent / "src").resolve()))

from pygpt_net.app import run as cli_run


def launch_gui() -> None:
    """Start the Tkinter GUI."""
    try:
        import tkinter as tk
        from gui.main_ui import MainUI
    except Exception as exc:
        raise RuntimeError(f"Unable to load GUI modules: {exc}") from exc

    root = tk.Tk()
    app = MainUI(root)
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
        "--version",
        action="store_true",
        help="Print pygpt_net version and exit",
    )
    args = parser.parse_args()

    # Warn if running on an unsupported operating system
    check_os_support()

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

