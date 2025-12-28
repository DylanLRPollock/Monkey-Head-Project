# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for fastapi/responses

"""Minimal subset of ``fastapi.responses`` used in the tests."""
from __future__ import annotations

from typing import Any, Iterable

__all__ = ["StreamingResponse", "HTMLResponse"]


class StreamingResponse:
    def __init__(
        self, content: Iterable[Any], *, media_type: str = "text/plain"
    ) -> None:
        self.content = content
        self.media_type = media_type

    def __iter__(self):  # pragma: no cover - used implicitly
        return iter(self.content)


class HTMLResponse:
    def __init__(
        self,
        content: str,
        *,
        status_code: int = 200,
        media_type: str = "text/html",
    ) -> None:
        self.content = content
        self.status_code = status_code
        self.media_type = media_type

    def __str__(self) -> str:  # pragma: no cover - convenience for debugging
        return self.content
