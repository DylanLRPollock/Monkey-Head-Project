"""Recovery, legacy-record, and pruning coverage for Honeycomb storage."""

from __future__ import annotations

import json

import pytest

from huey.honeycomb_storage import HoneycombStorage


def test_missing_record_is_a_noop_for_reads_and_removal(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)

    assert storage.get_record("default/missing") is None
    assert storage.load("default/missing") is None
    storage.remove("default/missing")
    assert storage.list_keys() == []
    assert list(tmp_path.iterdir()) == []


def test_legacy_record_without_timestamps_is_read_and_updated(tmp_path, monkeypatch):
    record_path = tmp_path / "archive" / "legacy.json"
    record_path.parent.mkdir()
    record_path.write_text(
        json.dumps({"key": "archive/legacy", "data": {"version": 1}}),
        encoding="utf-8",
    )
    storage = HoneycombStorage(base_dir=tmp_path)
    monkeypatch.setattr("huey.honeycomb_storage.time.time", lambda: 200.0)

    record = storage.get_record("archive/legacy")
    assert record is not None
    assert record.created_at == 200.0
    assert record.updated_at == 200.0

    updated = storage.store("archive/legacy", {"version": 2})
    assert updated.created_at == 200.0
    assert updated.updated_at == 200.0
    assert storage.load("archive/legacy") == {"version": 2}


def test_prune_removes_only_matching_expired_records_and_empty_dirs(
    tmp_path, monkeypatch
):
    storage = HoneycombStorage(base_dir=tmp_path)
    now = [100.0]
    monkeypatch.setattr("huey.honeycomb_storage.time.time", lambda: now[0])

    storage.store("archive/expired/one", {"value": 1})
    storage.store("archive/keep", {"value": 2})
    storage.store("active/expired", {"value": 3})
    now[0] = 200.0
    storage.store("archive/keep", {"value": 4})

    assert storage.prune("archive/", older_than=150.0) == 1
    assert storage.list_keys() == ["active/expired", "archive/keep"]
    assert (tmp_path / "archive" / "expired").exists() is False
    assert storage.prune("archive/", older_than=150.0) == 0


def test_context_manager_closes_storage_after_exception(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)

    with pytest.raises(RuntimeError, match="operation failed"), storage:
        storage.store("safe", {"before": "failure"})
        raise RuntimeError("operation failed")

    with pytest.raises(RuntimeError, match="closed"):
        storage.store("safe", {"after": "failure"})
    assert storage.load("safe") == {"before": "failure"}
