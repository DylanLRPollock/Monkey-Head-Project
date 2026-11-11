"""
banana_brain — single-GPU scheduler for HueyOS / Monkey-Head-Project.

Public API is the composition root (scripts/banana-brain_scheduler.py)
and the scheduler API (scheduler_api.SchedulerAPI). Everything else is
imported by the composition root and by tests.

This module deliberately imports nothing from its submodules at import
time. Every module except job_models pulls in aiohttp; importing them
eagerly here would mean that even `import huey.banana_brain` requires
the full runtime dependency set. Instead, callers import what they need:

    from huey.banana_brain.config import load_config
    from huey.banana_brain.scheduler import Scheduler
    ...

The package exposes one convenience re-export: BananaBrainConfig, since
it is used by every caller and has no third-party dependencies beyond
the stdlib plus (for load_config only) PyYAML. load_config is exported
as a function, not eagerly called.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__", "BananaBrainConfig", "load_config"]


def __getattr__(name: str):
    """
    Lazy re-export so importing this package does not require PyYAML.

    The pattern is documented in PEP 562. If you import BananaBrainConfig
    or load_config from the top-level package, we fetch it on first access.
    """
    if name == "BananaBrainConfig":
        from .config import BananaBrainConfig as _cfg
        return _cfg
    if name == "load_config":
        from .config import load_config as _load
        return _load
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
