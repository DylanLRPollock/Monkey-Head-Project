"""Minimal subset of the ``httpx`` API tailored for the test-suite."""
from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Any, Dict, Optional


class ASGITransport:
    def __init__(self, app: Any) -> None:
        self.app = app


@dataclass
class _Response:
    status_code: int
    payload: Any

    def json(self) -> Any:
        return self.payload


class AsyncClient(AbstractAsyncContextManager["AsyncClient"]):
    def __init__(self, *, transport: ASGITransport, base_url: str | None = None) -> None:
        self._transport = transport
        self._base_url = base_url

    async def __aenter__(self) -> "AsyncClient":  # pragma: no cover - exercised in tests
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        return None

    async def get(self, url: str, *, params: Optional[Dict[str, Any]] = None) -> _Response:
        return self._request("GET", url, params=params)

    async def post(
        self,
        url: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> _Response:
        return self._request("POST", url, params=params, json=json)

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> _Response:
        app = self._transport.app
        if hasattr(app, "handle_request"):
            response = app.handle_request(method, url, params=params or {}, json=json or {})
            payload = response.json()
            return _Response(status_code=response.status_code, payload=payload)
        raise RuntimeError("Provided app does not implement handle_request")
