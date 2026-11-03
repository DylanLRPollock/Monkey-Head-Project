"""Regression coverage for canonical Huey memory migration."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from huey.memory import indexing, ingestion, metadata, preload_data


@pytest.fixture
def memroot(tmp_path, monkeypatch):
    root = tmp_path / "memory"
    root.mkdir()
    monkeypatch.setenv("MEMORY_PATH", str(root))
    return root


def test_legacy_alias_identity():
    for name in ("indexing", "ingestion", "metadata", "preload_data"):
        assert importlib.import_module(f"huey.memory.PY.{name}") is (
            importlib.import_module(f"huey.memory.{name}")
        )


def test_txt_and_json_metadata(tmp_path):
    source = tmp_path / "note.txt"
    source.write_text("alpha", encoding="utf-8")
    record = ingestion.ingest_txt(source, store_copy=False)
    assert record["content"] == "alpha"
    assert record["metadata"]["sha256"] == hashlib.sha256(b"alpha").hexdigest()
    assert ingestion.ingest_md(source, store_copy=False)["kind"] == "md"
    js = tmp_path / "data.json"
    js.write_text('{"x": 1}', encoding="utf-8")
    assert ingestion.ingest_json(js, store_copy=False)["content"] == {"x": 1}


def test_copy_collision_preserves_original(tmp_path, memroot):
    first = tmp_path / "one" / "same.txt"
    first.parent.mkdir()
    first.write_text("old")
    dest = Path(ingestion.ingest_txt(first)["path"])
    assert Path(ingestion.ingest_txt(first)["path"]) == dest
    other = tmp_path / "two" / "same.txt"
    other.parent.mkdir()
    other.write_text("new")
    with pytest.raises(FileExistsError):
        ingestion.ingest_txt(other)
    assert dest.read_text() == "old"


def test_invalid_json_does_not_write(tmp_path, memroot):
    source = tmp_path / "bad.json"
    source.write_text("{not-json")
    with pytest.raises(json.JSONDecodeError):
        ingestion.ingest_json(source)
    assert not (memroot / "INGESTED").exists()


def test_media_summary_uses_probe_result(tmp_path, monkeypatch):
    source = tmp_path / "sound.wav"
    source.write_bytes(b"test")
    monkeypatch.setattr(
        metadata, "probe_media",
        lambda path: SimpleNamespace(duration_seconds=12.5),
    )
    assert "12.5" in metadata.file_summary(source)


def test_index_excludes_hidden_code_and_self(memroot):
    (memroot / "note.txt").write_text("alpha")
    (memroot / ".private.txt").write_text("hidden")
    (memroot / "PY").mkdir()
    (memroot / "PY" / "code.json").write_text('{"x": 1}')
    (memroot / "INDEX").mkdir()
    target = memroot / "INDEX" / "memory-index.json"
    target.write_text('[]')
    (memroot / "link.txt").symlink_to(memroot / "note.txt")
    assert indexing.discover_paths(memroot, index_path=target) == [memroot / "note.txt"]
    assert len(indexing.rebuild_index(memroot, index_path=target)) == 1
    assert len(indexing.rebuild_index(memroot, index_path=target)) == 1
    assert len(indexing.search_index("alpha", index_path=target)) == 1


def test_failed_atomic_replace_retains_old_index(tmp_path, monkeypatch):
    target = tmp_path / "index.json"
    target.write_text('[{"path": "old"}]')

    def fail_replace(source, destination):
        raise OSError("disk error")

    monkeypatch.setattr(indexing.os, "replace", fail_replace)
    with pytest.raises(OSError):
        indexing._save_index([{"path": "new"}], target)
    assert json.loads(target.read_text()) == [{"path": "old"}]
    assert not list(tmp_path.glob("*.tmp"))


def test_index_input_validation(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"invalid": true}')
    with pytest.raises(ValueError, match="Malformed"):
        indexing.update_index({"path": "test"}, index_path=path)
    with pytest.raises(ValueError, match="path"):
        indexing.update_index({}, index_path=path)


def test_preload_skips_code_and_keeps_data(memroot):
    for folder, name in (("PY", "code.py"), ("PDF", "paper.pdf")):
        (memroot / folder).mkdir()
        (memroot / folder / name).write_bytes(b"fixture")
    result = preload_data.load_memory()
    assert "PY" not in result
    assert len(result["PDF"]) == 1


def test_prompt_csv_header_and_comment(tmp_path, monkeypatch):
    source = tmp_path / "prompts.csv"
    source.write_text('# comment\nact,prompt,for_devs\nTest,"hello, world",FALSE\n')
    monkeypatch.setattr(preload_data, "_PROMPT_CANDIDATES", (source,))
    assert preload_data.load_prompts()[0]["prompt"] == "hello, world"


def test_cli_defaults_to_nonmutating_dry_run(memroot):
    (memroot / "one.txt").write_text("hello")
    script = Path(__file__).resolve().parents[1] / "scripts" / "memory_index.py"
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(memroot), "--json"],
        text=True, capture_output=True, check=True,
    )
    assert json.loads(result.stdout)["mode"] == "dry-run"
    assert not (memroot / "INDEX").exists()


def test_cli_explicit_write_required(memroot):
    script = Path(__file__).resolve().parents[1] / "scripts" / "memory_index.py"
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(memroot), "--write"],
        text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert "--index-path" in result.stderr
