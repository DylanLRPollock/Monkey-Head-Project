"""Fallback and boundary behavior for resilience and Honeycomb indexing."""

from __future__ import annotations

import pytest

from huey.core.resilience import (
    CrashRecoveryManager,
    EmergencyGovernanceController,
    EmergencyState,
    SystemdWatchdogClient,
)
from huey.honeycomb_index import HoneycombContentMapping, HoneycombIndex
from huey.os.honeycomb_storage import HoneycombRecord, HoneycombStorage


def test_watchdog_missing_or_unreachable_socket_is_best_effort(monkeypatch) -> None:
    assert SystemdWatchdogClient(notify_socket=None).ready() is False
    client = SystemdWatchdogClient(notify_socket="/missing/notify.sock")

    def fail_socket(*args, **kwargs):
        raise OSError("socket unavailable")

    monkeypatch.setattr("huey.core.resilience.socket.socket", fail_socket)
    assert client.ping() is False


def test_emergency_transitions_skip_essential_services_and_ignore_duplicates() -> None:
    controller = EmergencyGovernanceController(required_approvals=2)
    calls = []
    controller.register_service(
        "essential", stop=lambda: calls.append("essential-stop"), essential=True
    )
    controller.register_service("unmanaged", stop=lambda: calls.append("stop"))
    controller.register_service("no-start", stop=lambda: None)
    controller.register_service(
        "managed",
        stop=lambda: calls.append("managed-stop"),
        start=lambda: calls.append("managed-start"),
    )

    with pytest.raises(ValueError, match="reason"):
        controller.enter_emergency_mode(triggered_by="a", reason="", approvals=["b"])
    with pytest.raises(PermissionError):
        controller.enter_emergency_mode(
            triggered_by="a", reason="fault", approvals=["a"]
        )
    with pytest.raises(PermissionError):
        controller.enter_emergency_mode(
            triggered_by="a", reason="fault", approvals=["a", "a"]
        )

    controller.enter_emergency_mode(triggered_by="a", reason="fault", approvals=["b"])
    controller.enter_emergency_mode(
        triggered_by="duplicate", reason="ignored", approvals=[]
    )
    assert controller.state is EmergencyState.EMERGENCY
    assert calls == ["stop", "managed-stop"]
    controller.exit_emergency_mode(requested_by="a", approvals=["b"])
    controller.exit_emergency_mode(requested_by="a", approvals=[])
    assert calls[-1] == "managed-start"
    assert controller.status()["state"] == "normal"


def test_crash_manager_unknown_processes_and_disabled_restart_reason() -> None:
    manager = CrashRecoveryManager(history_limit=1)
    with pytest.raises(ValueError, match="history_limit"):
        CrashRecoveryManager(history_limit=0)
    with pytest.raises(KeyError, match="Unknown monitored process"):
        manager.toggle_auto_restart("missing", False)
    with pytest.raises(KeyError, match="Unknown monitored process"):
        manager.manual_restart("missing")

    manager.register_process("fails", health_check=lambda: False, restart=lambda: None)
    manager.set_auto_restart("fails", False)
    event = manager.poll()[0]
    assert event.restarted is False
    assert event.metadata["manual_override"] is True
    assert manager.has_process("fails")
    manager.unregister_process("fails")
    manager.unregister_process("fails")
    assert manager.has_process("fails") is False
    assert manager.statuses() == []
    assert manager.event_log() == [event]


def test_index_fallback_classification_custom_types_and_malformed_records(
    tmp_path,
) -> None:
    storage = HoneycombStorage(base_dir=tmp_path)
    index = HoneycombIndex(storage, extension_map={"foo": "CUSTOM"})
    assert index.infer_category(tmp_path / "unknown.foo") == "CUSTOM"
    assert index.infer_category(tmp_path / "unknown.xyz") == "XYZ"
    assert index.infer_category(tmp_path / "no-extension") is None
    assert index.infer_content_type(tmp_path / "no-extension") is None

    record = index.index_file(tmp_path / "unknown.xyz", metadata={"extra": True})
    assert record.key.startswith("misc/general/")
    assert "misc" in index.list_content_types()
    index.register_content_type(
        "custom",
        HoneycombContentMapping(
            comb="custom-comb", cell_prefix="items", categories=("CUSTOM",)
        ),
    )
    assert index.infer_content_type(tmp_path / "x.foo") == "custom"
    assert index.describe()["custom"]["categories"] == ["CUSTOM"]

    malformed = HoneycombRecord(
        key="misc/general/bad",
        data={
            "content_type": "misc",
            "payload": "scalar",
            "metadata": [1],
            "indexed_at": 2,
        },
        created_at=1,
        updated_at=3,
    )
    converted = index._to_index_record(malformed)
    assert converted is not None
    assert converted.payload == {"value": "scalar"}
    assert converted.metadata == {"value": [1]}


def test_index_skips_non_object_or_untyped_records_and_applies_limits(
    tmp_path, monkeypatch
) -> None:
    storage = HoneycombStorage(base_dir=tmp_path)
    index = HoneycombIndex(storage)
    good = HoneycombRecord(
        key="telemetry/logs/one",
        data={"content_type": "logs", "payload": {"n": 1}},
        created_at=1,
        updated_at=4,
    )
    missing_type = HoneycombRecord(
        key="telemetry/logs/two", data={"payload": {}}, created_at=2, updated_at=2
    )
    bad_data = HoneycombRecord(
        key="telemetry/logs/three", data="not a mapping", created_at=3, updated_at=3
    )
    monkeypatch.setattr(
        storage, "query", lambda _prefix: [good, missing_type, bad_data]
    )
    assert len(index.records_for_content_type("logs", limit=1)) == 1
    assert [item.key for item in index.records_since(0)] == ["telemetry/logs/one"]
    assert [item.key for item in index.records_since(0, content_type="logs")] == [
        "telemetry/logs/one"
    ]
