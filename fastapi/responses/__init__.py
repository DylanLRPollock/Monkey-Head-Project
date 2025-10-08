"""Minimal subset of ``fastapi.responses`` used in the tests."""
from __future__ import annotations

from typing import Any, Iterable

__all__ = ["StreamingResponse"]


class StreamingResponse:
    def __init__(self, content: Iterable[Any], *, media_type: str = "text/plain") -> None:
        self.content = content
        self.media_type = media_type

    def __iter__(self):  # pragma: no cover - used implicitly
        return iter(self.content)
