"""License acceptance helpers for GUI entrypoints."""

from __future__ import annotations

import json
from datetime import datetime, timezone
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


__all__ = ["accept_license"]
