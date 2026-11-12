"""
banana_brain — single-GPU scheduler for HueyOS / Monkey-Head-Project.

Public API is the composition root (scripts/banana-brain_scheduler.py)
and the scheduler API (scheduler_api.SchedulerAPI). Everything else is
imported by the composition root and by tests.

This module keeps runtime adapters lazy. The config module uses only the
standard library at import time, so its public configuration helpers can be
re-exported without requiring the runtime dependency set.

    from huey.banana_brain.config import load_config
    from huey.banana_brain.scheduler import Scheduler
    ...

The package exposes BananaBrainConfig and load_config as convenience
re-exports; PyYAML is imported only when load_config reads a file.
"""

from __future__ import annotations

from .config import BananaBrainConfig, load_config

__version__ = "0.1.0"
__all__ = ["BananaBrainConfig", "__version__", "load_config"]
