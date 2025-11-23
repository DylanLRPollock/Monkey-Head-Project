# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Honeycomb Index module (tests)

import time

from hueyos.honeycomb.index import HoneycombIndex
from hueyos.honeycomb.storage import HoneycombStorage


def test_index_records_by_content_type(tmp_path, monkeypatch):
    storage = HoneycombStorage(base_dir=tmp_path)
    index = HoneycombIndex(storage)

    monkeypatch.setattr(time, "time", lambda: 1_000.0)
    index.store_payload("logs", {"message": "old"}, cell_id="old")

    monkeypatch.setattr(time, "time", lambda: 2_000.0)
    index.store_payload("logs", {"message": "new"}, cell_id="new")

    records = index.records_for_content_type("logs")
    assert [record.payload["message"] for record in records] == ["new", "old"]

    recent = index.records_since(1_500.0, content_type="logs")
    assert len(recent) == 1
    assert recent[0].payload["message"] == "new"


def test_index_file_infers_content_type(tmp_path):
    storage = HoneycombStorage(base_dir=tmp_path)
    index = HoneycombIndex(storage)

    image = tmp_path / "photo.jpeg"
    image.write_bytes(b"data")

    record = index.index_file(image)
    assert record.key.startswith("media/images/")

    stored = storage.get_record(record.key)
    assert stored is not None
    assert stored.data["payload"]["content_type"] == "images"
