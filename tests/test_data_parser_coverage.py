"""Exercise content routing and fallback behavior in the data parser."""

from __future__ import annotations

from huey.data.parser import parse_data


def test_mapping_payload_is_copied():
    source = {"nested": [1]}
    parsed = parse_data(source)
    assert parsed == {"kind": "mapping", "data": source}
    assert parsed["data"] is not source


def test_text_and_json_payload_routing():
    assert parse_data(' {"ok": true} ') == {"kind": "json", "data": {"ok": True}}
    malformed = parse_data("{not json}")
    assert malformed["kind"] == "text"
    assert malformed["text"] == "{not json}"
    assert malformed["sentences"] == ["{not json}"]
    assert malformed["token_frequency"] == {"not": 1, "json": 1}


def test_bytes_decode_ignores_invalid_utf8():
    parsed = parse_data(b"hello\xff world", source="notes.txt")
    assert parsed["kind"] == "text"
    assert parsed["text"] == "hello world"


def test_pdf_bytes_are_routed_by_case_insensitive_suffix():
    parsed = parse_data(b"%PDF-1.4\nHello", source="document.PDF")
    assert parsed == {
        "kind": "pdf",
        "text": "%PDF-1.4 Hello",
        "line_count": 2,
        "characters": len("%PDF-1.4 Hello"),
    }
