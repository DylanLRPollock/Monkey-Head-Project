"""Success, validation and atomicity paths in canonical memory indexing."""

from __future__ import annotations

import json

import pytest

from huey.memory import indexing


def _create_symlink_or_skip(link, target):
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink support unavailable: {exc}")


def test_update_index_insert_replace_and_search(tmp_path):
    index_path = tmp_path / "INDEX" / "memory-index.json"
    first = {
        "path": "notes.txt",
        "kind": "text",
        "content": "Hydraulic design",
        "metadata": {"summary": "motor controller"},
    }
    assert indexing.update_index(first, index_path=index_path) == [first]
    assert index_path.is_file()
    assert indexing.search_index("HYDRAULIC", index_path=index_path) == [first]
    assert indexing.search_index("motor controller", index_path=index_path) == [first]

    replacement = {**first, "content": "Revised design"}
    assert indexing.update_index(replacement, index_path=index_path) == [replacement]
    assert indexing.search_index("hydraulic", index_path=index_path) == []
    assert indexing.search_index("revised", index_path=index_path) == [replacement]
    assert indexing.search_index("   ", index_path=index_path) == []


def test_index_missing_malformed_and_invalid_record(tmp_path):
    missing = tmp_path / "index.json"
    assert indexing._load_index(missing) == []
    with pytest.raises(ValueError, match="nonempty"):
        indexing.update_index({"path": ""}, index_path=missing)
    assert not missing.exists()

    missing.write_text(json.dumps({"path": "not-a-list"}), encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed"):
        indexing._load_index(missing)

    missing.write_text(json.dumps(["str-not-dict"]), encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed"):
        indexing._load_index(missing)


def test_discovery_skips_hidden_paths_code_and_symlinks(tmp_path):
    base = tmp_path / "memory"
    base.mkdir()
    expected = base / "notes.TXT"
    expected.write_text("hi", encoding="utf-8")
    (base / "ignore.py").write_text("pass", encoding="utf-8")
    (base / ".secret.md").write_text("hidden", encoding="utf-8")
    internal = base / "PY"
    internal.mkdir()
    (internal / "legacy.txt").write_text("skip", encoding="utf-8")
    link = base / "alias.md"
    _create_symlink_or_skip(link, expected)
    assert indexing.discover_paths(base) == [expected]
    with pytest.raises(NotADirectoryError):
        indexing.discover_paths(tmp_path / "absent")


def test_build_index_does_not_ingest_symlinks_or_index_file(monkeypatch, tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    doc = root / "notes.txt"
    doc.write_text("memo", encoding="utf-8")
    index_file = root / "index.json"
    alias = root / "alias.txt"
    _create_symlink_or_skip(alias, doc)
    observed = []

    def fake_ingest(path):
        observed.append(path)
        return {"path": str(path), "kind": "text"}

    monkeypatch.setattr(indexing, "_ingest_path", fake_ingest)
    inputs = [doc, index_file]
    if alias.is_symlink():
        inputs.append(alias)
    results = indexing.build_index(inputs, index_path=index_file)
    assert results == [{"path": str(doc), "kind": "text"}]
    assert observed == [doc]
    assert indexing._load_index(index_file) == results


def test_atomic_save_replaces_existing_payload(tmp_path):
    path = tmp_path / "index.json"
    path.write_text("stale", encoding="utf-8")
    results = [{"path": "new", "kind": "text"}]
    assert indexing._save_index(results, path) == path
    assert indexing._load_index(path) == results
    assert not list(tmp_path.glob("*.tmp"))
