# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Honeycomb Storage module (tests)

import time

import pytest

from huey.os.honeycomb.storage import HoneycombStorage


def test_store_list_and_remove(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)
    record = storage.store("alpha", {"a": 1})
    assert record.key == "alpha"
    assert storage.load("alpha") == {"a": 1}
    keys = storage.list_keys()
    assert "alpha" in keys
    assert storage.count() == 1
    storage.remove("alpha")
    assert storage.load("alpha") is None
    assert storage.count() == 0


def test_metrics_and_growth(tmp_path, monkeypatch):
    storage = HoneycombStorage(base_dir=tmp_path)

    monkeypatch.setattr(time, "time", lambda: 1_000.0)
    storage.store("media/images/one", {"payload": {"size": 10}})

    monkeypatch.setattr(time, "time", lambda: 1_500.0)
    storage.store("media/images/two", {"payload": {"size": 20}})

    monkeypatch.setattr(time, "time", lambda: 2_000.0)
    storage.store("telemetry/logs/three", {"payload": {"size": 5}})

    usage = storage.comb_usage()
    comb_names = {item["comb"] for item in usage}
    assert comb_names == {"media", "telemetry"}
    media_entry = next(item for item in usage if item["comb"] == "media")
    assert media_entry["cells"] == 2
    assert media_entry["oldest"] == 1_000.0
    assert media_entry["newest"] == 1_500.0

    metrics = storage.prefix_metrics("media/images/")
    assert metrics["cells"] == 2
    assert metrics["oldest"] == 1_000.0

    monkeypatch.setattr(time, "time", lambda: 2_500.0)
    growth = storage.growth_samples(window_days=1)
    assert any(sample["cells"] >= 1 for sample in growth)


def test_conversation_helpers(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)
    storage.append_conversation("chat", role="user", content="hello")
    storage.append_conversation("chat", role="assistant", content="hi")

    history = list(storage.iter_conversation("chat"))
    assert len(history) == 2
    assert history[0].data["role"] == "user"
    assert history[1].data["role"] == "assistant"

    results = storage.query("conversation/chat/")
    assert len(results) == 2


def test_store_rejects_invalid_keys(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)

    with pytest.raises(TypeError):
        storage.store(123, {})

    with pytest.raises(ValueError):
        storage.store("   ", {})

    with pytest.raises(ValueError):
        storage.store("/leading", {})


@pytest.mark.parametrize(
    "key", ["../outside", "safe/../outside", "safe/./outside", "safe\\..\\outside"]
)
def test_store_rejects_path_traversal_components(tmp_path, key):
    storage = HoneycombStorage(base_dir=tmp_path / "storage")

    with pytest.raises(ValueError, match="safe path"):
        storage.store(key, {"payload": "blocked"})

    assert not (tmp_path / "outside.json").exists()


def test_store_rejects_symlinked_comb_that_escapes_root(tmp_path):
    root = tmp_path / "storage"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)
    storage = HoneycombStorage(base_dir=root)

    with pytest.raises(ValueError, match="inside the storage root"):
        storage.store("linked/record", {"payload": "blocked"})

    assert not (outside / "record.json").exists()


def test_list_keys_ignores_symlinked_record_outside_root(tmp_path):
    root = tmp_path / "storage"
    record_dir = root / "default"
    record_dir.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text('{"key": "default/leaked", "data": "secret"}')
    (record_dir / "linked.json").symlink_to(outside)
    storage = HoneycombStorage(base_dir=root)

    assert storage.list_keys() == []
    assert storage.query("default/") == []


def test_store_after_close_raises(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)
    storage.close()

    with pytest.raises(RuntimeError):
        storage.store("alpha", {})


def test_failed_atomic_replace_preserves_record_and_cleans_temporary_file(
    tmp_path, monkeypatch
):
    from pathlib import Path

    storage = HoneycombStorage(base_dir=tmp_path)
    storage.store("alpha", {"version": 1})
    record_path = tmp_path / "default" / "alpha.json"
    original_bytes = record_path.read_bytes()

    def fail_replace(_self, _target):
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated replacement failure"):
        storage.store("alpha", {"version": 2})

    assert record_path.read_bytes() == original_bytes
    assert not list(tmp_path.rglob("*.tmp"))


def test_failed_serialization_preserves_record_and_cleans_temporary_file(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)
    storage.store("alpha", {"version": 1})
    record_path = tmp_path / "default" / "alpha.json"
    original_bytes = record_path.read_bytes()

    with pytest.raises(TypeError):
        storage.store("alpha", {"not-json": object()})

    assert record_path.read_bytes() == original_bytes
    assert not list(tmp_path.rglob("*.tmp"))
