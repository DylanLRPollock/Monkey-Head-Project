"""Sensor API routes extracted from the legacy API module."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Request, status

from huey.memory.PY.api import SensorRegistrationRequest

router = APIRouter(tags=["Sensors"])


@router.get("/sensors/plugins")
def sensor_plugins():
    from huey.memory.PY import api as legacy_api

    return legacy_api.sensor_plugins()


@router.get("/sensors")
def list_sensors():
    from huey.memory.PY import api as legacy_api

    return legacy_api.list_sensors()


@router.post("/sensors/register", status_code=status.HTTP_201_CREATED)
def register_sensor(payload: SensorRegistrationRequest, request: Request):
    from huey.memory.PY import api as legacy_api

    legacy_api.require_admin_api_auth(request)
    return legacy_api.register_sensor(payload)


@router.delete("/sensors/{sensor_name}")
def remove_sensor(sensor_name: str, request: Request):
    from huey.memory.PY import api as legacy_api

    legacy_api.require_admin_api_auth(request)
    return legacy_api.remove_sensor(sensor_name)


@router.post("/sensors/{sensor_name}/poll")
def poll_sensor(sensor_name: str):
    from huey.memory.PY import api as legacy_api

    return legacy_api.poll_sensor(sensor_name)


@router.post("/sensors/poll")
def poll_all_sensors():
    from huey.memory.PY import api as legacy_api

    return legacy_api.poll_all_sensors()


@router.get("/sensors/{sensor_name}/history")
def sensor_history(
    sensor_name: str,
    limit: Annotated[
        int, Query(ge=1, le=500, description="Maximum number of readings to return")
    ] = 50,
):
    from huey.memory.PY import api as legacy_api

    return legacy_api.sensor_history(sensor_name, limit=limit)


@router.get("/sensors/{sensor_name}/stream")
async def stream_sensor(sensor_name: str):
    from huey.memory.PY import api as legacy_api

    return await legacy_api.stream_sensor(sensor_name)


@router.get("/sensors/stream")
async def stream_all_sensors():
    from huey.memory.PY import api as legacy_api

    return await legacy_api.stream_all_sensors()


__all__ = [
    "list_sensors",
    "poll_all_sensors",
    "poll_sensor",
    "register_sensor",
    "remove_sensor",
    "router",
    "sensor_history",
    "sensor_plugins",
    "stream_all_sensors",
    "stream_sensor",
]
