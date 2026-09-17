#!/usr/bin/env python3
"""
# ---------------------------------------------------------------------------
# Monkey-Head-Project
# Component: HueyOS / Run
# Author: Dylan L.R. Pollock
# Documentation: https://www.dlrp.ca
#
# Philosophy: Breathing new life into old tech.
# ---------------------------------------------------------------------------
"""

"""Convenience proxy to expose the Huey runtime entry points at the project root.

This module:

* Ensures ``src/`` is on ``sys.path`` when running from a source checkout.
* Imports :mod:`huey.run`.
* Re-exports the public API of :mod:`huey.run` (its ``__all__``).
* Provides a script entry point so you can run:

    python run.py

which will delegate to ``huey.run.main()`` (or ``huey.run.cli()`` as a fallback).

The heavy lifting lives in :mod:`huey.run`; this file is intentionally thin so
``pip install -e .`` style workflows and ``python run.py`` calls both land in
the same place.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

# --- Locations -------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_PATH = _PROJECT_ROOT / "src"

# --- Errors ----------------------------------------------------------------


class RunError(SystemExit):
    """Exit with a clear, actionable message instead of a bare traceback."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        lines = [f"error: {message}"]
        if hint:
            lines.append(f"hint:  {hint}")
        super().__init__("\n".join(lines))


# --- sys.path bootstrap ----------------------------------------------------


def _bootstrap_src_path() -> None:
    """Prefer a local ``src/`` checkout over any installed copy of ``huey``.

    We insert at position 0 (not append) so an editable checkout wins over a
    site-packages install, matching the original behaviour. We only do this
    when the directory actually exists so a wheel install isn't penalised.
    """
    if not _SRC_PATH.is_dir():
        return

    src_str = str(_SRC_PATH)
    # Remove any existing occurrence (from a prior import or PYTHONPATH) and
    # reinsert at the front so precedence is deterministic.
    sys.path[:] = [p for p in sys.path if p != src_str]
    sys.path.insert(0, src_str)


_bootstrap_src_path()


# --- Runtime import --------------------------------------------------------


def _load_runtime_module() -> ModuleType:
    """Import and return the underlying :mod:`huey.run` module.

    Wrapped so that import-time failures (missing package, broken dependency,
    syntax error in the target) surface as a single actionable ``RunError``
    rather than a stack trace ending somewhere deep in importlib.
    """
    try:
        return importlib.import_module("huey.run")
    except ModuleNotFoundError as exc:
        missing = getattr(exc, "name", "") or "unknown"
        if missing == "huey" or missing.startswith("huey."):
            raise RunError(
                f"Unable to import 'huey.run' (missing module: {missing!r}).",
                f"Ensure {_SRC_PATH} exists and contains a 'huey' package, "
                "or install the project with `pip install -e .`.",
            ) from exc
        raise RunError(
            f"'huey.run' imported but requires a missing dependency: {missing!r}.",
            "Install the project's dependencies (e.g. `pip install -e .`).",
        ) from exc
    except ImportError as exc:  # pragma: no cover - defensive
        raise RunError(
            "Unable to import 'huey.run'.",
            "Check that 'src/huey/run.py' exists and imports cleanly.",
        ) from exc


_module = _load_runtime_module()

# Re-export the public API declared by huey.run.
__all__: list[str] = list(getattr(_module, "__all__", []))
globals().update({name: getattr(_module, name) for name in __all__})

# Convenience passthroughs when the underlying module exposes them.
__version__: str = getattr(_module, "__version__", "0.0.0")
__author__: str = getattr(_module, "__author__", "Dylan L.R. Pollock")


# --- Entry point resolution ------------------------------------------------


def _resolve_entry() -> Callable[[], object]:
    """Return the callable that ``python run.py`` should invoke.

    Prefers ``huey.run.main``; falls back to ``huey.run.cli``. Raises
    ``RunError`` if neither is present or if the candidate is not callable.
    """
    for name in ("main", "cli"):
        candidate = getattr(_module, name, None)
        if candidate is None:
            continue
        if not callable(candidate):
            raise RunError(
                f"'huey.run.{name}' exists but is not callable "
                f"(got {type(candidate).__name__}).",
                "Expose a function, not a value, under that name.",
            )
        return candidate  # type: ignore[return-value]

    raise RunError(
        "No 'main' or 'cli' entry point exposed by 'huey.run'.",
        "Add a `main()` (or `cli()`) function to src/huey/run.py.",
    )


def _main() -> int:
    """Entry point when executing ``python run.py``.

    Delegates to ``huey.run.main()`` if present, otherwise ``huey.run.cli()``.
    Normalises the return value to an integer exit status and translates
    common failure modes into clean diagnostics.
    """
    entry = _resolve_entry()

    try:
        result = entry()
    except KeyboardInterrupt:
        print("\nrun.py: interrupted", file=sys.stderr)
        return 130
    except BrokenPipeError:
        # Happens on `python run.py --help | head`. Silence the flush noise.
        try:
            sys.stdout.close()
        except Exception:
            pass
        return 0
    except SystemExit:
        # Let the callee own its own exit code, but stop the traceback dance.
        raise
    except Exception as exc:
        raise RunError(
            f"{type(exc).__name__} raised while running 'huey.run': {exc}",
            "Re-run with `python -X dev run.py` for the full traceback.",
        ) from exc

    # Convention: None -> 0, bool -> 0/1, int -> as-is, anything else -> 0.
    if result is None:
        return 0
    if isinstance(result, bool):
        return int(result)
    if isinstance(result, int):
        return result
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(_main())