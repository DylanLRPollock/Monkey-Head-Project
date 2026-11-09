"""Exercise the canonical honeycomb storage core and secondary index."""

from __future__ import annotations

import pytest

from huey.exceptions import StorageError
from huey.storage.honeycomb import HoneycombStore
from huey.storage.index import StorageIndex


def test_honeycomb_store_put_get_cache_miss_and_replication_plan(monkeypatch):
    store = HoneycombStore()
    payload = {"name": "Huey", "generation": 3}

    result = store.put("profile/huey", payload, labels=["profile", "robot"])

    assert result["key"] == "profile/huey"
    cluster = store.cluster_index.cluster_for("profile/huey")
    assert result["cluster"] == cluster
    assert result["replication"] == store.replication.plan(cluster)
    assert store.get("profile/huey") == payload

    # Force the compressed-record path rather than serving the in-memory cache.
    monkeypatch.setattr(store.cache, "get", lambda _key: None)
    assert store.get("profile/huey") == payload
    assert store.cache.snapshot()["profile/huey"]["value"] == payload


def test_honeycomb_store_unknown_get_and_delete_raise_storage_error():
    store = HoneycombStore()

    with pytest.raises(StorageError, match="Unknown storage key"):
        store.get("missing")

    with pytest.raises(StorageError, match="Unknown storage key"):
        store.delete("missing")


def test_honeycomb_store_delete_updates_record_index_and_cache():
    store = HoneycombStore()
    store.put("profile/huey", {"name": "Huey"}, labels=["profile"])

    store.delete("profile/huey")

    assert store.snapshot()["keys"] == []
    assert store.index.by_label("profile") == []
    assert store.cache.snapshot()["profile/huey"]["value"] is None


def test_honeycomb_snapshot_sorts_keys_and_reports_indexes():
    store = HoneycombStore()
    store.put("zeta", {"value": 2}, labels=["shared"])
    store.put("alpha", {"value": 1}, labels=["shared", "first"])

    snapshot = store.snapshot()

    assert snapshot["keys"] == ["alpha", "zeta"]
    assert snapshot["index"]["labels"] == {
        "shared": ["alpha", "zeta"],
        "first": ["alpha"],
    }
    assert set(snapshot["cache"]) == {"alpha", "zeta"}


def test_storage_index_handles_empty_labels_clusters_and_removal():
    index = StorageIndex()
    index.add("one")
    index.add("two", labels=["red", "red"], cluster="west")
    index.add("three", labels=["red"], cluster="west")

    assert index.by_label("red") == ["three", "two"]
    assert index.by_label("missing") == []
    assert index.by_cluster("west") == ["three", "two"]
    assert index.by_cluster("missing") == []

    index.remove("two")
    index.remove("absent")

    assert index.by_label("red") == ["three"]
    assert index.by_cluster("west") == ["three"]
    assert index.snapshot() == {
        "labels": {"red": ["three"], "first": []}
        if False
        else {"red": ["three"]},
        "clusters": {"west": ["three"]},
    }
