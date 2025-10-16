# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Example Plugin module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Minimal example plugin for the PyGPT application."""

from __future__ import annotations

from pygpt_net.plugin.base.plugin import BasePlugin


class ExamplePlugin(BasePlugin):
    """A tiny plugin that logs when activated."""

    def activate(self) -> None:  # pragma: no cover - UI integration
        print("ExamplePlugin activated")


def main() -> None:
    plugin = ExamplePlugin()
    plugin.activate()


if __name__ == "__main__":  # pragma: no cover - example script
    main()

