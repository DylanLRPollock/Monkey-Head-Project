"""SubOS microservice runtime."""
from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Dict, List

import uvicorn
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel

logger = logging.getLogger("subos-runtime")

app = FastAPI(
    title="Monkey Head SubOS",
    version="0.1.0",
    description="Microservices orchestrating AI processing, memory management, and sensor drivers.",
)

_sensor_data: Dict[str, float] = {"imu": 0.0, "lidar": 0.0, "pressure": 0.0}
_memory_events: List[str] = []


class TextPayload(BaseModel):
    text: str


class MemoryRequest(BaseModel):
    path: str
    tags: List[str]


class SensorResponse(BaseModel):
    readings: Dict[str, float]


async def _sensor_loop() -> None:
    counter = 0
    while True:
        counter += 1
        for key in list(_sensor_data):
            _sensor_data[key] = (counter % 360) / 10.0
        await asyncio.sleep(1)


@app.on_event("startup")
async def startup_event() -> None:  # pragma: no cover - runtime side effect
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    asyncio.create_task(_sensor_loop())


@app.post("/ai/process", summary="Run AI inference on text input")
def ai_process(payload: TextPayload) -> Dict[str, str]:
    logger.info("Processing AI payload with %d characters", len(payload.text))
    return {"processed": payload.text.upper()}


@app.post("/memory/snapshot", summary="Persist structured memory events")
def memory_snapshot(request: MemoryRequest, background_tasks: BackgroundTasks) -> Dict[str, int]:
    def _write_event() -> None:
        entry = f"{request.path}:{','.join(request.tags)}"
        _memory_events.append(entry)
        logger.debug("Memory event recorded: %s", entry)

    background_tasks.add_task(_write_event)
    return {"scheduled": len(_memory_events) + 1}


@app.get("/sensors/readings", response_model=SensorResponse)
def sensor_readings() -> SensorResponse:
    return SensorResponse(readings=_sensor_data.copy())


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok", "services": "ai,memory,sensors"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the SubOS microservices gateway")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
