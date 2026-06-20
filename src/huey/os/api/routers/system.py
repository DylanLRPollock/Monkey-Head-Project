"""System and health API routes extracted from the legacy API module."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter

router = APIRouter(tags=["System"])


@router.get("/healthz")
def healthz() -> Dict[str, str]:
    """Lightweight probe used by orchestrators to ensure the API is responsive."""

    return {"status": "ok", "service": "hueyos"}


@router.get("/status/system")
@router.get("/system/status")
def system_status() -> dict:
    """Return operating system, hardware, and configuration details for HueyOS."""

    from huey.memory.PY.api import _build_system_status

    return _build_system_status().model_dump()


__all__ = ["router", "healthz", "system_status"]
