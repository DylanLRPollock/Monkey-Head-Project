"""Temporary, explicit opt-in compatibility for the historical PyHuey stub.

The real PyGPT application runs separately; see huey.integrations.pygpt_cli.
This compatibility API is scheduled for removal on 2027-05-01.
"""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .function_registry import (
    describe_functions,
    discover_function_modules,
    ensure_registered_functions,
)


@dataclass(frozen=True)
class PyHueySource:
    name: str
    path: Path
    package_path: Path
    kind: str
    description: str
    import_name: str | None = None

    @property
    def exists(self) -> bool:
        return self.package_path.is_dir()

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "path": str(self.path),
            "package_path": str(self.package_path),
            "import_name": self.import_name,
            "kind": self.kind,
            "description": self.description,
            "exists": self.exists,
        }


def project_root(start: Path | None = None) -> Path:
    cursor = (start or Path(__file__)).resolve()
    if cursor.is_file():
        cursor = cursor.parent
    for parent in (cursor, *cursor.parents):
        if (parent / "pyproject.toml").is_file() and (parent / "src").is_dir():
            return parent
    return Path(__file__).resolve().parents[4]


def candidate_sources(
    extra_paths: Iterable[str | os.PathLike[str]] | None = None,
) -> list[PyHueySource]:
    """Return only the packaged test stub; external paths are never searched."""
    root = project_root()
    return [
        PyHueySource(
            name="package",
            path=root / "src",
            package_path=root / "src" / "huey" / "connectors" / "pyhuey",
            kind="compatibility",
            description="Deprecated PyHuey test stub, not upstream PyGPT.",
            import_name="huey.connectors.pyhuey",
        )
    ]


def candidate_src_paths(
    extra_paths: Iterable[str | os.PathLike[str]] | None = None,
) -> list[Path]:
    return [item.path for item in candidate_sources(extra_paths)]


def available_sources(
    extra_paths: Iterable[str | os.PathLike[str]] | None = None,
) -> list[PyHueySource]:
    return [item for item in candidate_sources(extra_paths) if item.exists]


def prepare_pygpt(
    module_name: str = "pygpt_net",
    *,
    search_paths: Iterable[Path] | None = None,
    source: str | None = None,
) -> bool:
    """Opt into the legacy stub by explicitly selecting ``source='package'``.

    Never discover or import upstream PyGPT or mutate sys.path. Do not replace
    a previously imported, unrelated module with the stub.
    """
    if source != "package" or module_name != "pygpt_net" or search_paths is not None:
        return False
    module = importlib.import_module("huey.connectors.pyhuey")
    existing = sys.modules.get(module_name)
    if existing is not None and existing is not module:
        raise RuntimeError("pygpt_net is already loaded; refusing to replace it")
    sys.modules[module_name] = module
    ensure_registered_functions()
    return True


def pyhuey_status(
    module_name: str = "pygpt_net", *, source: str | None = None
) -> dict[str, object]:
    prepared = prepare_pygpt(module_name, source=source)
    module = sys.modules.get(module_name) if prepared else None
    functions = describe_functions()
    return {
        "prepared": prepared,
        "module": module_name,
        "version": getattr(module, "__version__", None) if module else None,
        "module_file": str(getattr(module, "__file__", "")) if module else None,
        "active_source": candidate_sources()[0].as_dict() if prepared else "unresolved",
        "candidates": [item.as_dict() for item in candidate_sources()],
        "custom_function_modules": discover_function_modules(),
        "custom_functions": functions,
        "custom_function_count": len(functions),
    }


def reset_pygpt_state() -> None:
    """Compatibility no-op; preparation is no longer cached."""


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
