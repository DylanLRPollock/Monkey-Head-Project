# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.12.2025
# ==================================================
"""Home Assistant API integration helpers."""

from __future__ import annotations

import os
from typing import Any, Mapping

import requests

DEFAULT_BASE_URL = os.environ.get("HASS_URL", "http://localhost:8123")
DEFAULT_TOKEN = os.environ.get("HASS_TOKEN", "")


def _build_headers(token: str | None = None) -> dict[str, str]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def call_service(
    domain: str,
    service: str,
    data: Mapping[str, Any] | None = None,
    *,
    base_url: str = DEFAULT_BASE_URL,
    token: str = DEFAULT_TOKEN,
) -> Any:
    """Call a Home Assistant service and return the JSON response."""
    url = f"{base_url}/api/services/{domain}/{service}"
    resp = requests.post(url, headers=_build_headers(token), json=data or {})
    resp.raise_for_status()
    return resp.json()


def get_state(
    entity_id: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
    token: str = DEFAULT_TOKEN,
) -> Any:
    """Return state data for ``entity_id`` via the REST API."""
    url = f"{base_url}/api/states/{entity_id}"
    resp = requests.get(url, headers=_build_headers(token))
    resp.raise_for_status()
    return resp.json()
