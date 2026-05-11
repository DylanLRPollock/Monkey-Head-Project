"""Network API routes extracted from the legacy API module."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Network"])


@router.get("/network/status")
def network_status():
    from huey.memory.PY import api as legacy_api

    return legacy_api.network_status()


@router.post("/network/ensure")
def ensure_network_connectivity():
    from huey.memory.PY import api as legacy_api

    return legacy_api.ensure_network_connectivity()


__all__ = ["router", "network_status", "ensure_network_connectivity"]
