# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey/pygpt_net

"""Minimal stub of the :mod:`pygpt_net` package for integration tests."""

from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
from typing import Final

__all__ = ["__version__"]

__version__ = "2.6.67"

_NLTK_ENV_VAR: Final[str] = "NLTK_DATA"
_CUSTOM_ENV_VAR: Final[str] = "PYGPT_NLTK_DATA_DIR"


def _ensure_private_nltk_data() -> None:
    """Force NLTK data into a per-user directory to avoid shared caches."""

    if os.environ.get(_NLTK_ENV_VAR):
        return

    target_dir = Path(
        os.environ.get(
            _CUSTOM_ENV_VAR,
            Path.home() / ".cache" / "pygpt_net" / "nltk_data",
        )
    )

    try:
        target_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError:
        # If the directory cannot be created we silently fall back to the
        # upstream defaults rather than break runtime imports.
        return

    os.environ[_NLTK_ENV_VAR] = str(target_dir)

    nltk_spec = importlib.util.find_spec("nltk")
    if nltk_spec is None:
        return

    nltk = importlib.import_module("nltk")
    resolved_dir = str(target_dir)
    if resolved_dir not in nltk.data.path:
        nltk.data.path.insert(0, resolved_dir)


_ensure_private_nltk_data()
