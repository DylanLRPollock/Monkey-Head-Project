from monkey_head.honeycomb_storage import HoneycombStorage


def test_store_and_load(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)
    storage.store("alpha", {"a": 1})
    assert storage.load("alpha") == {"a": 1}
    keys = storage.list_keys()
    assert "alpha" in keys
    storage.remove("alpha")
    assert storage.load("alpha") is None
