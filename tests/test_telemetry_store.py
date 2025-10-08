from huey.hardware.plugins import SensorReading
from monkey_head.utils.persistence import TelemetryStore


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
