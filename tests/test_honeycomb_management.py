# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Honeycomb Management module (tests)

import subprocess

import pytest

from monkey_head.honeycomb_backup import perform_rsync_snapshot, restore_snapshot
from monkey_head.honeycomb_index import HoneycombIndex
from monkey_head.honeycomb_monitor import HoneycombMonitor
from monkey_head.honeycomb_retention import RetentionPolicy, parse_duration
from monkey_head.honeycomb_storage import HoneycombStorage


def test_honeycomb_index_maps_extensions(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)
    index = HoneycombIndex(storage)
    image_path = tmp_path / "photo.jpeg"
    image_path.write_bytes(b"data")
    record = index.index_file(image_path)
    assert record.key.startswith("media/images/")
    payload = storage.load(record.key)
    assert payload["payload"]["content_type"] == "images"
    assert payload["payload"]["name"] == "photo.jpeg"


def test_honeycomb_monitor_reports_usage(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)
    index = HoneycombIndex(storage)
    storage.store("media/images/abc", {"payload": {}})
    storage.store("telemetry/logs/def", {"payload": {}})
    monitor = HoneycombMonitor(storage, index=index)
    report = monitor.build_usage_report()
    assert report["totals"]["cells"] == 2
    assert len(report["summary"]) >= 2
    assert any(item["content_type"] == "images" for item in report["content_types"])


def test_retention_policy_prunes_old_cells(tmp_path, monkeypatch):
    import monkey_head.honeycomb_retention as retention_module
    import monkey_head.honeycomb_storage as storage_module

    storage = HoneycombStorage(base_dir=tmp_path)
    index = HoneycombIndex(storage)

    monkeypatch.setattr(storage_module.time, "time", lambda: 1000.0)
    index.store_payload("logs", {"message": "old"}, cell_id="old")

    monkeypatch.setattr(storage_module.time, "time", lambda: 2000.0)
    index.store_payload("logs", {"message": "new"}, cell_id="new")

    policy = RetentionPolicy(content_types={"logs": 500.0})
    monkeypatch.setattr(retention_module.time, "time", lambda: 2000.0)

    removed = policy.apply(storage, index=index)
    assert removed["logs"] == 1
    assert storage.count("telemetry/logs/") == 1


def test_parse_duration_supports_units():
    assert parse_duration("10s") == 10
    assert parse_duration("5m") == 300
    with pytest.raises(ValueError):
        parse_duration("abc")


def test_backup_helpers_build_rsync_commands(tmp_path, monkeypatch):
    import monkey_head.honeycomb_backup as backup_module

    source = tmp_path / "memory"
    destination = tmp_path / "snapshots"
    source.mkdir()
    (source / "data.txt").write_text("hello")

    monkeypatch.setattr(backup_module, "_resolve_rsync", lambda: "/usr/bin/rsync")

    commands = {}

    def fake_run(cmd, check, capture_output, text):
        commands["cmd"] = cmd

        class Result:
            stdout = "ok"
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = perform_rsync_snapshot(
        destination=destination,
        source=source,
        timestamp="20240101-000000",
    )

    assert commands["cmd"][0] == "/usr/bin/rsync"
    assert commands["cmd"][-2] == f"{source.resolve()}/"
    assert result.snapshot == destination / "20240101-000000"

    commands.clear()
    restore_result = restore_snapshot(
        destination / "20240101-000000", tmp_path / "restore"
    )
    assert commands["cmd"][0] == "/usr/bin/rsync"
    assert restore_result.snapshot == (tmp_path / "restore")
