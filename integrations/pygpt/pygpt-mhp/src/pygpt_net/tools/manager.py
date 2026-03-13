# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Manager module (repo/pygpt-MHP/src/pygpt_net/tools)

"""Minimal Monkey Head manager tool for the PyGPT stub environment."""

from __future__ import annotations

from typing import Dict


class MonkeyManager:
    """Expose Monkey Head automation hooks inside the PyGPT GUI."""

    def __init__(self) -> None:
        self.id = "monkey_manager"
        self.window = None

    def setup_menu(self) -> Dict[str, object]:  # pragma: no cover - simple mapping
        """Return a dictionary describing actions; currently empty."""

        return {}


__all__ = ["MonkeyManager"]
