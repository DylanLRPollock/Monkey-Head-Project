"""Utility helpers for wiring pygpt_net into Monkey Head.

The helpers in this module centralise how we discover and register local copies
of ``pygpt_net``.  They are intentionally lightweight so they can be imported
without pulling heavy GUI dependencies during CLI or test runs.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Iterable, List

_PYGPT_PREPARED = False


def candidate_src_paths(extra_paths: Iterable[str | os.PathLike[str]] | None = None) -> List[Path]:
    """Return ordered candidate directories that may house ``pygpt_net`` sources."""

    project_root = Path(__file__).resolve().parents[2]
    default_paths = [
        project_root / "pygpt",
        project_root / "pygpt" / "src",
        project_root / "src" / "huey" / "memory" / "PY" / "src",
        project_root / "repo" / "pygpt-MHP" / "src",
    ]

    env_paths: list[Path] = []
    env_value = os.environ.get("PYGPT_EXTRA_PATHS")
    if env_value:
        for chunk in env_value.split(os.pathsep):
            if chunk.strip():
                env_paths.append(Path(chunk).expanduser())

    additional_paths = [Path(path) for path in extra_paths or []]

    seen: set[str] = set()
    ordered_paths: list[Path] = []
    for path in (*default_paths, *env_paths, *additional_paths):
        resolved = str(path)
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered_paths.append(path)
    return ordered_paths


def prepare_pygpt(
    module_name: str = "pygpt_net",
    *,
    search_paths: Iterable[Path] | None = None,
) -> bool:
    """Ensure the requested module can be imported.

    When the module is not installed site-wide the function will iteratively add
    known vendor locations to ``sys.path`` until the import succeeds.
    """

    global _PYGPT_PREPARED
    if _PYGPT_PREPARED:
        return True

    try:
        importlib.import_module(module_name)
    except Exception:
        for candidate in candidate_src_paths(search_paths):
            if not candidate.exists():
                continue
            resolved = str(candidate.resolve())
            if resolved not in sys.path:
                sys.path.insert(0, resolved)
            try:
                importlib.import_module(module_name)
            except Exception:
                continue
            _PYGPT_PREPARED = True
            return True
        return False
    _PYGPT_PREPARED = True
    return True


def reset_pygpt_state() -> None:
    """Reset cached preparation state (useful for tests)."""

    global _PYGPT_PREPARED
    _PYGPT_PREPARED = False


__all__ = ["candidate_src_paths", "prepare_pygpt", "reset_pygpt_state"]
