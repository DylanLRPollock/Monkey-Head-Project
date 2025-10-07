from monkey_head.honeycomb_storage import HoneycombStorage


def test_store_load_and_conversation(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)
    storage.store("alpha", {"a": 1})
    stored = storage.load("alpha")
    assert stored == {"a": 1}

    storage.append_conversation(
        "alpha",
        "Spark",
        "analysis",
        "Review complete",
        metadata={"decision": "approve"},
    )

    history = storage.get_conversation("alpha")
    assert len(history) == 1
    assert history[0].agent == "Spark"
    assert history[0].metadata["decision"] == "approve"

    updated_payload = storage.load("alpha")
    assert updated_payload["conversation_count"] == 1
    assert updated_payload["last_speaker"] == "Spark"

    keys = storage.list_keys()
    assert "alpha" in keys

    storage.remove("alpha")
    assert storage.load("alpha") is None
    assert storage.get_conversation("alpha") == []
