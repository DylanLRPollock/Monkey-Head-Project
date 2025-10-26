# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for src/huey

"""Public surface for the HueyOS package."""

from __future__ import annotations

from pathlib import Path
from typing import List

from pkgutil import extend_path

__all__ = ["api"]

# Ensure the package exposes modules from the legacy ``huey`` tree that still
# lives at the repository root.  The CLI relies on helpers such as
# :mod:`huey.utils`, so we extend ``__path__`` to include that directory when
# available.  ``extend_path`` keeps compatibility with editable installs where
# ``src`` already appears on ``sys.path``.
__path__ = extend_path(__path__, __name__)

_project_root = Path(__file__).resolve().parents[2]
_legacy_dir = _project_root / "huey"
if _legacy_dir.exists():
    legacy_path = str(_legacy_dir)
    if isinstance(__path__, list):
        search_path: List[str] = __path__
    else:  # pragma: no cover - fallback for extend_path returning other types
        search_path = list(__path__)  # type: ignore[arg-type]
    if legacy_path not in search_path:
        search_path.append(legacy_path)
        __path__ = search_path  # type: ignore[assignment]
