"""Data loading helpers for files and in-memory payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def load_data(source: str | Path | dict[str, Any]) -> dict[str, object]:
    if isinstance(source, dict):
        return dict(source)
    path = Path(source)
    text = load_text(path)
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return {"path": str(path), "text": text}


__all__ = ["load_data", "load_text"]
