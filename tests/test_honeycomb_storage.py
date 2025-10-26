# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Honeycomb Storage module (tests)

import time

import pytest

from monkey_head.honeycomb_storage import HoneycombStorage


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


def test_store_after_close_raises(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)
    storage.close()

    with pytest.raises(RuntimeError):
        storage.store("alpha", {})
