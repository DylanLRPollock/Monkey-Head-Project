# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Run compatibility wrapper (src)

"""Expose legacy runtime entry points under :mod:`huey.run`."""

from __future__ import annotations

from .memory.PY import run as _run

# NOTE(v101.1-migration): Compatibility wrapper for the legacy ``huey.run``
# module while implementation stays in ``src/huey/memory/PY``.
main = _run.main
run_module = _run.run_module
minimal_run = _run.minimal_run
run_sys_code = _run.run_sys_code
launch_install_gui = _run.launch_install_gui
launch_gui = _run.launch_gui
print_pyhuey_info = _run.print_pyhuey_info

__all__ = [
    "main",
    "run_module",
    "minimal_run",
    "run_sys_code",
    "launch_install_gui",
    "launch_gui",
    "print_pyhuey_info",
]


def __getattr__(name: str):
    """Delegate unknown attributes to the legacy runtime module."""

    return getattr(_run, name)
