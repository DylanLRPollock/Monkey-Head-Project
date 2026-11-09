"""Behavioral coverage for the small public utility modules."""

from __future__ import annotations

import os
import zipfile

import pytest

from huey.tools.backup import create_backup_archive
from huey.tools.encryption import FernetVault
from huey.tools.file_watcher import FileWatcher
from huey.tools.hashing import fingerprint_mapping, sha256_text
from huey.tools.metrics import MetricsRegistry
from huey.tools.profiler import ProfileTimer
from huey.tools.scheduler import JobScheduler, ScheduledJob
from huey.tools.testing import assert_mapping_subset, build_fixture_payload


def test_backup_archive_contains_source_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "notes.txt").write_text("Huey data", encoding="utf-8")

    archive_path = create_backup_archive(source, tmp_path / "backup")

    assert archive_path.endswith(".zip")
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.read("notes.txt") == b"Huey data"


def test_fernet_vault_round_trip_and_rejects_invalid_token():
    pytest.importorskip("cryptography.fernet")
    vault = FernetVault()

    token = vault.encrypt_text("private note")

    assert vault.decrypt_text(token) == "private note"
    with pytest.raises(Exception):
        vault.decrypt_text("not-a-valid-fernet-token")


def test_file_watcher_reports_added_modified_and_removed_files(tmp_path):
    root = tmp_path / "watched"
    root.mkdir()
    existing = root / "existing.txt"
    existing.write_text("before", encoding="utf-8")
    watcher = FileWatcher(root)

    assert watcher.snapshot() == {"existing.txt": existing.stat().st_mtime}
    assert watcher.changes() == {"added": [], "modified": [], "removed": []}

    existing.write_text("after", encoding="utf-8")
    os.utime(existing, (existing.stat().st_atime, existing.stat().st_mtime + 5))
    (root / "new.txt").write_text("new", encoding="utf-8")
    (root / "removed.txt").write_text("gone", encoding="utf-8")
    watcher.snapshot()
    (root / "removed.txt").unlink()

    assert watcher.changes() == {
        "added": [],
        "modified": [],
        "removed": ["removed.txt"],
    }


def test_file_watcher_detects_changes_since_previous_snapshot(tmp_path):
    root = tmp_path / "watched"
    root.mkdir()
    watcher = FileWatcher(root)

    assert watcher.changes() == {"added": [], "modified": [], "removed": []}
    (root / "new.txt").write_text("new", encoding="utf-8")

    assert watcher.changes() == {
        "added": ["new.txt"],
        "modified": [],
        "removed": [],
    }


def test_hashing_helpers_are_stable_and_order_independent():
    assert sha256_text("huey") == (
        "e7c6f7f6dff8d6d76f5d17f9a6e0f3c3e5d9fb9afaaed7d6f0cbf234c4d5c2d9"
    )
    assert fingerprint_mapping({"b": 2, "a": 1}) == fingerprint_mapping(
        {"a": 1, "b": 2}
    )
    assert fingerprint_mapping({"a": 1}) != fingerprint_mapping({"a": 2})


def test_metrics_registry_accumulates_sets_and_returns_copy():
    registry = MetricsRegistry()

    assert registry.increment("requests") == 1.0
    assert registry.increment("requests", 2.5) == 3.5
    assert registry.set("temperature", 42.0) == 42.0
    snapshot = registry.snapshot()
    snapshot["requests"] = -1

    assert registry.snapshot() == {"requests": 3.5, "temperature": 42.0}


def test_profile_timer_uses_fixed_start_and_stop_times(monkeypatch):
    import huey.tools.profiler as profiler

    times = iter((12.5, 18.0))
    monkeypatch.setattr(profiler, "perf_counter", lambda: next(times))
    timer = ProfileTimer("startup", started_at=10.0)

    assert timer.elapsed == 2.5
    assert timer.stop() == 2.5
    assert timer.finished_at == 12.5
    assert timer.elapsed == 2.5


def test_scheduler_runs_due_jobs_once_and_records_result():
    calls = []
    scheduler = JobScheduler()
    scheduler.register(
        ScheduledJob("refresh", 10, lambda: calls.append("refresh") or "done")
    )

    assert scheduler.tick(now=9.0) == [
        {"name": "refresh", "result": "done", "ran_at": 9.0}
    ]
    assert calls == ["refresh"]
    assert scheduler.tick(now=18.9) == []
    assert scheduler.tick(now=19.0) == [
        {"name": "refresh", "result": "done", "ran_at": 19.0}
    ]
    assert calls == ["refresh", "refresh"]


def test_scheduler_does_not_mark_job_run_when_handler_raises():
    scheduler = JobScheduler()

    def fail():
        raise RuntimeError("temporary failure")

    job = ScheduledJob("failing", 1, fail)
    scheduler.register(job)

    with pytest.raises(RuntimeError, match="temporary failure"):
        scheduler.tick(now=5.0)

    assert job.last_run == 0.0


def test_scaffold_testing_helpers_apply_overrides_and_validate_subset():
    payload = build_fixture_payload(name="custom", extra=True)

    assert payload == {
        "name": "custom",
        "status": "ready",
        "priority": 1,
        "extra": True,
    }
    assert_mapping_subset({"name": "custom", "priority": 1}, payload)

    with pytest.raises(AssertionError, match="Missing key: absent"):
        assert_mapping_subset({"absent": 1}, payload)
    with pytest.raises(AssertionError, match="Unexpected value for 'name'"):
        assert_mapping_subset({"name": "wrong"}, payload)
