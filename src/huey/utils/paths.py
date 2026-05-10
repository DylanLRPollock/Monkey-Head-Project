"""Filesystem helpers for managing shared project directories."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SRC_ROOT = _PROJECT_ROOT / "src"


def _expand_path(value: str) -> Path:
    """Expand ``value`` to an absolute :class:`Path` relative to the project."""

    expanded = Path(os.path.expanduser(value))
    if expanded.is_absolute():
        return expanded
    return (_PROJECT_ROOT / expanded).resolve()


def get_memory_path(create: bool = True) -> Path:
    """Return the centralised memory directory used by the project.

    The location can be overridden with the ``MEMORY_PATH`` environment variable.
    If unset, the function prefers an existing ``memory`` directory at the project
    root, then falls back to the vendored ``src/huey/memory`` tree. When ``create``
    is ``True`` (the default) the returned directory is created if it does not
    already exist.
    """

    env_value = os.environ.get("MEMORY_PATH")
    if env_value:
        memory_path = _expand_path(env_value)
        if memory_path.exists() and not memory_path.is_dir():
            raise NotADirectoryError(f"MEMORY_PATH is not a directory: {memory_path}")
        if create:
            memory_path.mkdir(parents=True, exist_ok=True)
        return memory_path

    preferred = _PROJECT_ROOT / "memory"
    if preferred.is_dir():
        if create:
            preferred.mkdir(parents=True, exist_ok=True)
        return preferred

    packaged = _SRC_ROOT / "huey" / "memory"
    if packaged.exists():
        if create:
            packaged.mkdir(parents=True, exist_ok=True)
        return packaged

    if create:
        preferred.mkdir(parents=True, exist_ok=True)
    return preferred


def ensure_subdirectory(*parts: str) -> Path:
    """Return a subdirectory of :func:`get_memory_path` creating it if needed."""

    base = get_memory_path(create=True)
    target = base.joinpath(*parts)
    target.mkdir(parents=True, exist_ok=True)
    return target


def get_logs_dir() -> Path:
    """Return the log directory inside the memory path, creating it if missing."""

    return ensure_subdirectory("LOGS")


def memory_candidates(extra: Iterable[Path] | None = None) -> list[Path]:
    """Return a list of candidate memory directories for backwards compatibility."""

    candidates = []
    env_value = os.environ.get("MEMORY_PATH")
    if env_value:
        candidates.append(_expand_path(env_value))
    preferred = _PROJECT_ROOT / "memory"
    if preferred.is_dir():
        candidates.append(preferred)
    candidates.append(_SRC_ROOT / "huey" / "memory")
    if extra:
        candidates.extend(extra)
    seen: set[Path] = set()
    unique: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique
