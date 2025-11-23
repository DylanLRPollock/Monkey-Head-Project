# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Telemetry Store module (tests)

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
REPO_STR = str(REPO_ROOT)
SRC_STR = str(SRC_ROOT)
if REPO_STR not in sys.path:
    sys.path.insert(0, REPO_STR)
if SRC_STR not in sys.path:
    # Insert after the repository root so our vendored ``huey`` package wins
    sys.path.insert(1 if sys.path else 0, SRC_STR)

try:  # pragma: no cover - exercised indirectly when the package is available
    from huey.hardware.plugins import SensorReading
except ModuleNotFoundError:  # pragma: no cover - fallback for isolated test runs

    @dataclass
    class SensorReading:  # type: ignore[override]
        name: str
        value: Any
        timestamp: Optional[float] = None
        provenance: Optional[Dict[str, Any]] = None


from hueyos.utils.persistence import TelemetryStore


def test_telemetry_store_sensor_and_ai(tmp_path):
    store = TelemetryStore(tmp_path / "telemetry.db")
    reading = SensorReading(
        name="temperature",
        value=42.5,
        timestamp=1234.0,
        provenance={"plugin": "dummy"},
    )
    store.log_sensor_reading(reading)

    store.log_ai_result(
        prompt="Hello",
        response="World",
        model="llama3",
        backend="ollama",
        instruction="Rewrite",
        metadata={"confidence": 0.8},
        status="success",
    )

    sensors = store.fetch_recent_sensor_readings()
    assert sensors and sensors[0].name == "temperature"
    assert sensors[0].value == 42.5

    interactions = store.fetch_recent_ai_results()
    assert interactions and interactions[0].model == "llama3"
    assert interactions[0].metadata.get("confidence") == 0.8

    events = store.fetch_recent_events()
    assert events == []


def test_telemetry_store_handles_invalid_sensor_timestamp(tmp_path):
    class DummyReading:
        name = "temperature"
        value = 21.0
        timestamp = "invalid"

    store = TelemetryStore(tmp_path / "telemetry.db")
    store.log_sensor_reading(DummyReading())

    readings = store.fetch_recent_sensor_readings()
    assert readings
    assert isinstance(readings[0].timestamp, float)
