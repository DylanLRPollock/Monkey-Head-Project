# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Compatibility shim for huey/pygpt_net

"""Compatibility shim delegating legacy imports to :mod:`huey.connectors.pyhuey`."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, Final

_CANONICAL_MODULE: Final[str] = "huey.connectors.pyhuey"
_CANONICAL_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1] / "connectors" / "pyhuey"
)

__path__ = [str(_CANONICAL_PATH)]
if __spec__ is not None:  # pragma: no branch - importlib always sets this
    __spec__.submodule_search_locations = __path__

_impl = import_module(_CANONICAL_MODULE)

__all__ = list(getattr(_impl, "__all__", ()))
__version__ = getattr(_impl, "__version__", None)


def __getattr__(name: str) -> Any:
    """Delegate unknown attributes to :mod:`huey.connectors.pyhuey`."""

    return getattr(_impl, name)


def __dir__() -> list[str]:  # pragma: no cover - convenience helper
    return sorted(set(globals()) | set(dir(_impl)))
