# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Home Assistant module (src/monkey_head/services)

"""Minimal Home Assistant API helpers used by the test-suite."""

from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    import requests  # type: ignore[assignment]
except Exception:  # pragma: no cover - import guard
    requests = None  # type: ignore[assignment]

__all__ = ["call_service", "get_state"]


def _build_headers(token: str | None) -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _require_requests() -> None:
    if requests is None:
        raise RuntimeError("The 'requests' package is required for Home Assistant integrations")


def call_service(
    domain: str,
    service: str,
    payload: Dict[str, Any] | None = None,
    *,
    base_url: str = "http://localhost:8123",
    token: str | None = None,
) -> Dict[str, Any]:
    """Invoke a Home Assistant service and return the JSON payload."""

    _require_requests()
    url = f"{base_url.rstrip('/')}/api/services/{domain}/{service}"
    response = requests.post(url, json=payload or {}, headers=_build_headers(token), timeout=10)
    response.raise_for_status()
    return response.json()


def get_state(
    entity_id: str,
    *,
    base_url: str = "http://localhost:8123",
    token: str | None = None,
) -> Dict[str, Any]:
    """Return the state dictionary for ``entity_id``."""

    _require_requests()
    url = f"{base_url.rstrip('/')}/api/states/{entity_id}"
    response = requests.get(url, headers=_build_headers(token), timeout=10)
    response.raise_for_status()
    return response.json()
