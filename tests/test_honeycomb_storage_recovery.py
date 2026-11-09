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


def test_store_update_preserves_creation_time_and_key_filters(tmp_path, monkeypatch):
    storage = HoneycombStorage(base_dir=tmp_path)
    now = [100.0]
    monkeypatch.setattr("huey.honeycomb_storage.time.time", lambda: now[0])

    first = storage.store("media/images/one", {"size": 1})
    now[0] = 200.0
    updated = storage.store("media/images/one", {"size": 2})
    storage.store("media/audio/two", {"size": 3})

    assert updated.created_at == first.created_at
    assert updated.updated_at == 200.0
    assert storage.list_keys(prefix="media/images/") == ["media/images/one"]
    assert storage.count(prefix="media/audio/") == 1
    storage.remove("media/images/one")
    assert not (tmp_path / "media" / "images").exists()
    assert storage.list_keys() == ["media/audio/two"]


def test_usage_metrics_and_growth_ignore_nonmatching_prefixes(tmp_path, monkeypatch):
    storage = HoneycombStorage(base_dir=tmp_path)
    now = [1_700_000_000.0]
    monkeypatch.setattr("huey.honeycomb_storage.time.time", lambda: now[0])
    storage.store("media/images/one", {"name": "picture"})
    now[0] += 60
    storage.store("media/images/two", {"name": "another"})
    storage.store("telemetry/logs/one", {"status": "ok"})

    usage = storage.comb_usage()
    media = next(item for item in usage if item["comb"] == "media")
    assert media["cells"] == 2
    assert media["payload_bytes"] > 0
    assert media["oldest"] == 1_700_000_000.0
    assert media["newest"] == 1_700_000_060.0

    metrics = storage.prefix_metrics("media/images/")
    assert metrics["cells"] == 2
    assert metrics["payload_bytes"] == media["payload_bytes"]
    assert metrics["oldest"] == media["oldest"]
    assert metrics["newest"] == media["newest"]
    assert storage.prefix_metrics("missing/") == {
        "cells": 0,
        "payload_bytes": 0,
        "oldest": None,
        "newest": None,
    }
    samples = storage.growth_samples(window_days=1)
    assert sum(sample["cells"] for sample in samples) == 3


def test_conversation_iteration_and_query_are_sorted_and_limited(tmp_path, monkeypatch):
    storage = HoneycombStorage(base_dir=tmp_path)
    now = [100.0]
    monkeypatch.setattr("huey.honeycomb_storage.time.time", lambda: now[0])

    first = storage.append_conversation(
        "chat", role="user", content="hello", metadata={"cell_id": "first"}
    )
    now[0] = 200.0
    second = storage.append_conversation(
        "chat", role="assistant", content="hi", metadata={"cell_id": "second"}
    )

    assert first.data["metadata"]["role"] == "user"
    assert [record.key for record in storage.iter_conversation("chat")] == [
        first.key,
        second.key,
    ]
    assert storage.query("conversation/chat/", limit=1) == [second]
    assert storage.query("absent/") == []


def test_context_manager_closes_storage_after_exception(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)

    with pytest.raises(RuntimeError, match="operation failed"), storage:
        storage.store("safe", {"before": "failure"})
        raise RuntimeError("operation failed")

    with pytest.raises(RuntimeError, match="closed"):
        storage.store("safe", {"after": "failure"})
    assert storage.load("safe") == {"before": "failure"}
