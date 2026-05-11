"""Power API routes extracted from the legacy API module."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Power"])


@router.get("/power/battery")
def battery_status():
    from huey.memory.PY import api as legacy_api

    return legacy_api.battery_status()


@router.get("/power/should-shutdown")
def power_should_shutdown():
    from huey.memory.PY import api as legacy_api

    return legacy_api.power_should_shutdown()


@router.post("/power/shutdown")
def trigger_shutdown():
    from huey.memory.PY import api as legacy_api

    return legacy_api.trigger_shutdown()


__all__ = ["router", "battery_status", "power_should_shutdown", "trigger_shutdown"]
