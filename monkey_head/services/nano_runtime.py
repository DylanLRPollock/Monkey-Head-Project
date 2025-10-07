"""NanoOS runtime for low-level task orchestration."""
from __future__ import annotations

import argparse
import asyncio
import logging
import random
import time
from typing import Dict, List

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger("nanoos-runtime")

app = FastAPI(
    title="Monkey Head NanoOS",
    version="0.1.0",
    description="Manages deterministic control loops and microcontroller bridges.",
)

_task_state: Dict[str, float] = {"motor_loop": time.time(), "power_watchdog": time.time(), "telemetry_mux": time.time()}
_events: List[str] = []


class TaskStatus(BaseModel):
    name: str
    last_heartbeat: float
    healthy: bool


class TasksResponse(BaseModel):
    tasks: List[TaskStatus]


async def _control_loop(name: str, interval: float) -> None:
    while True:
        await asyncio.sleep(interval)
        jitter = random.uniform(-0.01, 0.01)
        _task_state[name] = time.time() + jitter
        logger.debug("Heartbeat for %s", name)


@app.on_event("startup")
async def on_startup() -> None:  # pragma: no cover - runtime side effect
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    asyncio.create_task(_control_loop("motor_loop", 0.05))
    asyncio.create_task(_control_loop("power_watchdog", 0.5))
    asyncio.create_task(_control_loop("telemetry_mux", 0.25))


@app.get("/tasks", response_model=TasksResponse)
def list_tasks() -> TasksResponse:
    now = time.time()
    payload = [
        TaskStatus(name=name, last_heartbeat=value, healthy=now - value < 1.0)
        for name, value in _task_state.items()
    ]
    return TasksResponse(tasks=payload)


@app.post("/tasks/reset/{task_name}", summary="Restart a control loop")
def reset_task(task_name: str) -> Dict[str, str]:
    if task_name not in _task_state:
        return {"status": "unknown", "task": task_name}
    _task_state[task_name] = time.time()
    _events.append(f"reset:{task_name}:{_task_state[task_name]}")
    logger.info("Reset request for %s", task_name)
    return {"status": "reset", "task": task_name}


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    unhealthy = [name for name, ts in _task_state.items() if time.time() - ts >= 1.0]
    status = "ok" if not unhealthy else "degraded"
    return {"status": status, "unhealthy": ",".join(unhealthy)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the NanoOS control runtime")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
