#!/usr/bin/env python3
"""Helpers for wrappers exposing remembered Python scripts from ``src/huey/memory/PY``."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

_REPO_MARKERS = ("pyproject.toml", "run.py")
_MEMORY_DIR = Path("src") / "huey" / "memory" / "PY"


def find_repo_root(start_path: Path) -> Path:
    cursor = start_path.resolve()
    if cursor.is_file():
        cursor = cursor.parent

    for candidate in (cursor, *cursor.parents):
        if all((candidate / marker).exists() for marker in _REPO_MARKERS):
            return candidate

    raise RuntimeError(f"Could not locate the repository root from '{start_path}'.")


def memory_directory(start_path: Path | None = None) -> Path:
    repo_root = find_repo_root(start_path or Path(__file__).resolve().parent)
    return repo_root / _MEMORY_DIR


def available_memory_python_scripts(start_path: Path | None = None) -> list[str]:
    return sorted(
        path.name
        for path in memory_directory(start_path).glob("*.py")
        if path.name != "__init__.py"
    )


def run_memory_python(script_name: str, *, start_path: Path | None = None) -> None:
    repo_root = find_repo_root(start_path or Path(__file__).resolve().parent)
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    target = repo_root / _MEMORY_DIR / script_name
    if not target.is_file():
        raise SystemExit(f"Memory Python script not found: {target}")

    runpy.run_path(str(target), run_name="__main__")
