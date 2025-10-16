# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: App module (huey/pygpt_net)

"""Stub application runner compatible with Monkey Head integration tests."""

from __future__ import annotations

from typing import Iterable


def run(*, tools: Iterable[object] | None = None) -> None:
    """Simulate launching the PyGPT GUI with the provided tools."""

    for tool in tools or ():
        setup = getattr(tool, "setup_menu", None)
        if callable(setup):
            setup()
