#!/usr/bin/env python3
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Run module

"""Convenience proxy to expose the Huey runtime entry points at the project root.

This module:

* Ensures ``src/`` is on ``sys.path`` when running from a source checkout.
* Imports :mod:`huey.run`.
* Re-exports the public API of :mod:`huey.run` (its ``__all__``).
* Provides a script entry point so you can run:

    python run.py

which will delegate to ``huey.run.main()`` (or ``huey.run.cli()`` as a fallback).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import List

_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_PATH = _PROJECT_ROOT / "src"

# Prefer local src/ over any installed copy, but do not break if it is missing.
if _SRC_PATH.is_dir():
    src_str = str(_SRC_PATH)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


def _load_runtime_module() -> ModuleType:
    """Import and return the underlying :mod:`huey.run` module.

    Wrapped so we can provide a clearer error message if import fails.
    """
    try:
        return importlib.import_module("huey.run")
    except ImportError as exc:  # pragma: no cover - defensive
        raise RuntimeError(
            "Unable to import 'huey.run'. "
            "Ensure the 'src' directory exists and the 'huey' package is importable."
        ) from exc


_module = _load_runtime_module()

# Re-export the public API of huey.run
__all__: List[str] = list(getattr(_module, "__all__", []))
globals().update({name: getattr(_module, name) for name in __all__})


def _main() -> int:
    """Entry point when executing ``python run.py``.

    Delegates to ``huey.run.main()`` if present, otherwise falls back
    to ``huey.run.cli()``. If neither exists, exits with a clear error.
    """
    # Prefer a conventional `main` entry point.
    entry = getattr(_module, "main", None)
    if callable(entry):
        result = entry()  # type: ignore[call-arg]
        return result if isinstance(result, int) else 0

    # Fallback to a `cli` function if present.
    entry = getattr(_module, "cli", None)
    if callable(entry):
        result = entry()  # type: ignore[call-arg]
        return result if isinstance(result, int) else 0

    raise SystemExit("No 'main' or 'cli' entry point exposed by 'huey.run'.")


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(_main())
