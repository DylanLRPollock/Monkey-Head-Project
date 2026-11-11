"""Cover Honeycomb storage path and cleanup edge cases."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from huey.honeycomb_storage import HoneycombStorage


@pytest.mark.parametrize(
    ("key", "error", "message"),
    [
        (None, TypeError, "keys must be strings"),
        ("", ValueError, "keys must not be empty"),
        ("   ", ValueError, "keys must not be empty"),
        ("/cell", ValueError, "Comb portion"),
        ("../cell", ValueError, "safe path component"),
        ("safe/", ValueError, "Cell portion"),
        ("safe/../cell", ValueError, "safe path components"),
    ],
)
def test_split_key_and_path_validation_reject_malformed_keys(
    tmp_path: Path, key, error, message
):
    storage = HoneycombStorage(base_dir=tmp_path)
    with pytest.raises(error, match=message):
        storage._record_path(key)


def test_default_location_uses_memory_path_environment(monkeypatch, tmp_path):
    memory_root = tmp_path / "custom-memory"
    monkeypatch.setenv("MEMORY_PATH", str(memory_root))

    storage = HoneycombStorage()

    assert storage._base_dir == (memory_root / "LOGS" / "honeycomb").resolve()
    assert storage._base_dir.is_dir()


@pytest.mark.parametrize("preferred_exists", [True, False])
def test_default_location_selects_existing_project_memory_tree(
    monkeypatch, preferred_exists
):
    monkeypatch.delenv("MEMORY_PATH", raising=False)
    root = Path(__file__).resolve().parents[1]
    preferred = (root / "memory").resolve()
    packaged = (root / "src" / "huey" / "memory").resolve()

    def exists(path):
        return path == (preferred if preferred_exists else packaged)

    monkeypatch.setattr(Path, "exists", exists)
    target = HoneycombStorage._default_base_dir()
    expected = preferred if preferred_exists else packaged
    assert target == expected / "LOGS" / "honeycomb"


def test_record_path_preserves_existing_extension_and_key_from_path_errors(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)
    assert (
        storage._record_path("comb/already.json") == tmp_path / "comb" / "already.json"
    )

    with pytest.raises(ValueError, match="Invalid record path"):
        storage._key_from_path(tmp_path / "single.json")
    assert storage._key_from_path(tmp_path / "comb" / "extensionless") == (
        "comb/extensionless"
    )


def test_remove_missing_file_and_skip_disappeared_record(tmp_path, monkeypatch):
    storage = HoneycombStorage(base_dir=tmp_path)
    storage.remove("missing")

    storage.store("comb/record", {"value": 1})
    monkeypatch.setattr(storage, "_read_record", lambda _path: None)
    assert storage.list_keys() == []


def test_missing_storage_root_and_record_are_ignored(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)
    missing_record = tmp_path / "comb" / "missing.json"
    assert storage._read_record(missing_record) is None

    tmp_path.rmdir()
    assert list(storage._iter_record_paths()) == []


def test_prune_skips_recent_and_already_removed_records(tmp_path, monkeypatch):
    storage = HoneycombStorage(base_dir=tmp_path)
    now = [100.0]
    monkeypatch.setattr(time, "time", lambda: now[0])
    old = storage.store("comb/old", {"value": 1})
    now[0] = 200.0
    recent = storage.store("comb/recent", {"value": 2})
    assert old.updated_at < recent.updated_at

    record_path = storage._record_path(old.key)
    original_unlink = Path.unlink

    def unlink_then_report_race(path, *args, **kwargs):
        if path == record_path:
            original_unlink(path, *args, **kwargs)
            raise FileNotFoundError(path)
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", unlink_then_report_race)
    assert storage.prune("comb/", older_than=150.0) == 0
    assert storage.get_record(recent.key) is not None


def test_payload_size_falls_back_to_string_for_non_json_values():
    class NonJsonValue:
        def __str__(self):
            return "not-json"

    assert HoneycombStorage._payload_size(NonJsonValue()) == 10


def test_growth_samples_omit_records_older_than_the_window(tmp_path, monkeypatch):
    storage = HoneycombStorage(base_dir=tmp_path)
    now = [100_000.0]
    monkeypatch.setattr(time, "time", lambda: now[0])
    storage.store("comb/old", {"value": "outside window"})

    now[0] = 200_000.0
    assert storage.growth_samples(window_days=0) == []


def test_metrics_handle_records_enumerated_newest_first(tmp_path, monkeypatch):
    storage = HoneycombStorage(base_dir=tmp_path)
    now = [200.0]
    monkeypatch.setattr(time, "time", lambda: now[0])
    storage.store("comb/a-new", {"value": 2})

    now[0] = 100.0
    storage.store("comb/z-old", {"value": 1})

    usage = storage.comb_usage()[0]
    metrics = storage.prefix_metrics("comb/")
    assert usage["oldest"] == metrics["oldest"] == 100.0
    assert usage["newest"] == metrics["newest"] == 200.0
