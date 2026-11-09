# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Honeycomb Management module (tests)

import pytest

from huey.os.honeycomb.backup import perform_rsync_snapshot, restore_snapshot
from huey.os.honeycomb.index import HoneycombIndex
from huey.os.honeycomb.monitor import HoneycombMonitor
from huey.os.honeycomb.retention import RetentionPolicy, parse_duration
from huey.os.honeycomb.storage import HoneycombStorage


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


def test_retention_policy_prunes_by_age():
    policy = RetentionPolicy(max_age="500s")

    assert policy.should_prune(1000.0, now=2000.0)
    assert not policy.should_prune(1600.0, now=2000.0)


def test_parse_duration_supports_units():
    assert parse_duration("10s") == 10
    assert parse_duration("5m") == 300
    with pytest.raises(ValueError):
        parse_duration("abc")


def test_backup_helpers_copy_snapshot_and_restore(tmp_path):
    source = tmp_path / "memory"
    destination = tmp_path / "snapshots"
    source.mkdir()
    (source / "data.txt").write_text("hello")

    result = perform_rsync_snapshot(
        destination=destination,
        source=source,
        label="20240101-000000",
    )

    snapshot = destination / "20240101-000000"
    assert result.destination == snapshot
    assert result.files_copied == 1
    assert (snapshot / "data.txt").read_text() == "hello"

    restore_dir = tmp_path / "restore"
    restored = restore_snapshot(snapshot, restore_dir)
    assert restored.destination == restore_dir.resolve()
    assert restored.files_copied == 1
    assert (restore_dir / "data.txt").read_text() == "hello"
