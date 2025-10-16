# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Example Tool module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Tiny custom tool usable with the PyGPT GUI."""

from __future__ import annotations

from typing import Dict

from PySide6.QtGui import QAction

from pygpt_net.tools.base import BaseTool


class EchoTool(BaseTool):
    """Simple tool that prints a message when triggered."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id = "echo_tool"

    def setup_menu(self) -> Dict[str, QAction]:  # pragma: no cover - UI usage
        action = QAction("Echo", self.window)
        action.triggered.connect(lambda: print("EchoTool activated"))
        return {"echo": action}


def main() -> None:
    tool = EchoTool()
    for action in tool.setup_menu().values():
        action.trigger()  # invoke action callback


if __name__ == "__main__":  # pragma: no cover - example script
    main()

