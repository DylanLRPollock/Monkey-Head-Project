"""License acceptance helpers for GUI entrypoints."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any


def _load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    with config_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def accept_license(config_path: str | Path, license_hash: str) -> None:
    path = Path(config_path)
    config = _load_config(path)
    config["license.accepted"] = True
    config["license.accepted_at"] = datetime.now(timezone.utc).isoformat()
    config["license.hash"] = license_hash
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, sort_keys=True)


def show_license_gui(config_path: str | Path = "config/pygpt_net/config.json") -> None:
    """Delegate to the maintained legacy GUI implementation when available."""

    legacy_module = import_module("huey.memory.PY.license_gui")
    legacy_module.show_license_gui(config_path)


__all__ = ["accept_license", "show_license_gui"]
