"""Utility helpers for wiring PyHuey/PyGPT-net into Monkey Head.

The helpers in this module centralise how we discover and register local copies
of ``pygpt_net``.  They are intentionally lightweight so they can be imported
without pulling heavy GUI dependencies during CLI or test runs.
"""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

_PYGPT_PREPARED = False
_PYGPT_ACTIVE_SOURCE: "PyHueySource | None" = None


@dataclass(frozen=True)
class PyHueySource:
    """A possible source tree for the ``pygpt_net`` package."""

    name: str
    path: Path
    package_path: Path
    kind: str
    description: str

    @property
    def exists(self) -> bool:
        return self.package_path.is_dir()

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "path": str(self.path),
            "package_path": str(self.package_path),
            "kind": self.kind,
            "description": self.description,
            "exists": self.exists,
        }


def project_root(start: Path | None = None) -> Path:
    """Return the repository root for a source checkout."""

    cursor = (start or Path(__file__)).resolve()
    if cursor.is_file():
        cursor = cursor.parent

    for parent in (cursor, *cursor.parents):
        if (parent / "pyproject.toml").is_file() and (parent / "src").is_dir():
            return parent
        if (parent / ".git").exists():
            return parent

    return Path(__file__).resolve().parents[4]


def _normalise_source(value: str | None) -> str:
    source = (value or os.environ.get("PYHUEY_SOURCE") or "auto").strip().lower()
    aliases = {
        "": "auto",
        "local": "package",
        "packaged": "package",
        "stub": "package",
        "src": "package",
        "submodule": "pyhuey",
        "integration": "pyhuey",
        "integrations": "pyhuey",
        "mhp": "vendor",
        "pygpt-mhp": "vendor",
        "vendor-mhp": "vendor",
        "site": "installed",
        "site-packages": "installed",
        "pip": "installed",
    }
    return aliases.get(source, source)


def candidate_sources(
    extra_paths: Iterable[str | os.PathLike[str]] | None = None,
) -> list[PyHueySource]:
    """Return ordered PyHuey/PyGPT-net source candidates."""

    root = project_root()
    sources = [
        PyHueySource(
            name="package",
            path=root / "src" / "huey",
            package_path=root / "src" / "huey" / "pygpt_net",
            kind="packaged",
            description="Lightweight PyGPT-net compatibility package shipped with HueyOS.",
        ),
        PyHueySource(
            name="pyhuey",
            path=root / "integrations" / "pyhuey" / "src",
            package_path=root / "integrations" / "pyhuey" / "src" / "pygpt_net",
            kind="submodule",
            description="Full PyHuey submodule source tree.",
        ),
        PyHueySource(
            name="vendor",
            path=root / "vendor" / "pygpt" / "pygpt-mhp" / "src",
            package_path=root / "vendor" / "pygpt" / "pygpt-mhp" / "src" / "pygpt_net",
            kind="vendor",
            description="Vendored lightweight pygpt-MHP mirror.",
        ),
        PyHueySource(
            name="vendor-upstream",
            path=root / "vendor" / "pygpt" / "py-gpt" / "src",
            package_path=root / "vendor" / "pygpt" / "py-gpt" / "src" / "pygpt_net",
            kind="vendor",
            description="Vendored upstream py-gpt placeholder mirror.",
        ),
        PyHueySource(
            name="legacy-root",
            path=root / "pygpt",
            package_path=root / "pygpt" / "pygpt_net",
            kind="legacy",
            description="Historical root-level PyGPT checkout.",
        ),
        PyHueySource(
            name="legacy-root-src",
            path=root / "pygpt" / "src",
            package_path=root / "pygpt" / "src" / "pygpt_net",
            kind="legacy",
            description="Historical root-level PyGPT src checkout.",
        ),
        PyHueySource(
            name="legacy-repo",
            path=root / "repo" / "pygpt-MHP" / "src",
            package_path=root / "repo" / "pygpt-MHP" / "src" / "pygpt_net",
            kind="legacy",
            description="Historical repo/pygpt-MHP checkout.",
        ),
    ]

    env_paths: list[Path] = []
    env_value = os.environ.get("PYGPT_EXTRA_PATHS")
    if env_value:
        for chunk in env_value.split(os.pathsep):
            if chunk.strip():
                env_paths.append(Path(chunk).expanduser())

    for index, path in enumerate((*env_paths, *(extra_paths or ())), start=1):
        source_path = Path(path).expanduser()
        sources.append(
            PyHueySource(
                name=f"extra-{index}",
                path=source_path,
                package_path=source_path / "pygpt_net",
                kind="extra",
                description="Operator-provided PyGPT-net source path.",
            )
        )

    seen: set[str] = set()
    ordered: list[PyHueySource] = []
    for source in sources:
        key = str(source.path)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(source)
    return ordered


def candidate_src_paths(
    extra_paths: Iterable[str | os.PathLike[str]] | None = None,
) -> List[Path]:
    """Return ordered candidate directories that may house ``pygpt_net`` sources."""

    return [source.path for source in candidate_sources(extra_paths)]


def available_sources(
    extra_paths: Iterable[str | os.PathLike[str]] | None = None,
) -> list[PyHueySource]:
    """Return source candidates that currently contain ``pygpt_net``."""

    return [source for source in candidate_sources(extra_paths) if source.exists]


def _source_matches(source: PyHueySource, preference: str) -> bool:
    if preference == "auto":
        return True
    if preference == "vendor":
        return source.kind == "vendor"
    return source.name == preference or source.kind == preference


def _try_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
    except Exception:
        return False
    return True


def prepare_pygpt(
    module_name: str = "pygpt_net",
    *,
    search_paths: Iterable[Path] | None = None,
    source: str | None = None,
) -> bool:
    """Ensure the requested module can be imported.

    When the module is not installed site-wide the function will iteratively add
    known vendor locations to ``sys.path`` until the import succeeds.
    """

    global _PYGPT_ACTIVE_SOURCE, _PYGPT_PREPARED
    preference = _normalise_source(source)

    if _PYGPT_PREPARED:
        return True

    if preference in {"auto", "installed"} and _try_import(module_name):
        _PYGPT_PREPARED = True
        _PYGPT_ACTIVE_SOURCE = None
        return True

    if preference == "installed":
        return False

    for candidate in candidate_sources(search_paths):
        if not _source_matches(candidate, preference):
            continue
        if not candidate.exists:
            continue
        resolved = str(candidate.path.resolve())
        if resolved not in sys.path:
            sys.path.insert(0, resolved)
        if _try_import(module_name):
            _PYGPT_PREPARED = True
            _PYGPT_ACTIVE_SOURCE = candidate
            return True

    return False


def pyhuey_status(
    module_name: str = "pygpt_net",
    *,
    source: str | None = None,
) -> dict[str, object]:
    """Return a lightweight status report for the PyHuey integration."""

    prepared = prepare_pygpt(module_name, source=source)
    module = sys.modules.get(module_name)
    return {
        "prepared": prepared,
        "module": module_name,
        "version": getattr(module, "__version__", None) if module else None,
        "module_file": str(getattr(module, "__file__", "")) if module else None,
        "active_source": (
            _PYGPT_ACTIVE_SOURCE.as_dict()
            if _PYGPT_ACTIVE_SOURCE
            else "installed" if prepared else "unresolved"
        ),
        "candidates": [source.as_dict() for source in candidate_sources()],
    }


def reset_pygpt_state() -> None:
    """Reset cached preparation state (useful for tests)."""

    global _PYGPT_ACTIVE_SOURCE, _PYGPT_PREPARED
    _PYGPT_PREPARED = False
    _PYGPT_ACTIVE_SOURCE = None


__all__ = [
    "PyHueySource",
    "available_sources",
    "candidate_sources",
    "candidate_src_paths",
    "prepare_pygpt",
    "project_root",
    "pyhuey_status",
    "reset_pygpt_state",
]
