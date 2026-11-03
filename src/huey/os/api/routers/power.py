"""Power API routes extracted from the legacy API module."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

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
def trigger_shutdown(request: Request):
    from huey.memory.PY import api as legacy_api

    legacy_api.require_strong_api_auth(request)
    if request.headers.get("x-huey-confirm") != "shutdown":
        raise HTTPException(
            status_code=403,
            detail="Explicit shutdown confirmation required (X-Huey-Confirm: shutdown).",
        )
    return legacy_api.trigger_shutdown(confirmed=True, actor_role="admin")


__all__ = ["battery_status", "power_should_shutdown", "router", "trigger_shutdown"]
