# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Auto Sort module (tests)

from pathlib import Path

import pytest

from hueyos.utils.auto_sort import auto_sort_memory


def _prepare_raw(memory_root: Path) -> Path:
    raw = memory_root / "RAW"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "document.pdf").write_text("pdf")
    (raw / "notes.txt").write_text("txt")
    (raw / "script.py").write_text("print('hi')")
    return raw


def test_auto_sort_moves_files(monkeypatch, tmp_path):
    memory_root = tmp_path / "memory"
    monkeypatch.setenv("MEMORY_PATH", str(memory_root))
    raw = _prepare_raw(memory_root)
    summary = auto_sort_memory()
    assert (memory_root / "PDF" / "document.pdf").exists()
    assert (memory_root / "TXT" / "notes.txt").exists()
    assert (memory_root / "PY" / "script.py").exists()
    assert summary["skipped"] == []
    assert not any(item.exists() for item in raw.iterdir())


def test_auto_sort_dry_run(monkeypatch, tmp_path):
    memory_root = tmp_path / "memory"
    monkeypatch.setenv("MEMORY_PATH", str(memory_root))
    raw = _prepare_raw(memory_root)
    summary = auto_sort_memory(dry_run=True)
    assert "document.pdf" in " ".join(summary["moved"])
    assert all(item.is_file() for item in raw.iterdir())


def test_auto_sort_missing_source(monkeypatch, tmp_path):
    memory_root = tmp_path / "memory"
    monkeypatch.setenv("MEMORY_PATH", str(memory_root))
    with pytest.raises(FileNotFoundError):
        auto_sort_memory(source_dir=memory_root / "does-not-exist")


def test_auto_sort_skips_hidden_files(monkeypatch, tmp_path):
    memory_root = tmp_path / "memory"
    monkeypatch.setenv("MEMORY_PATH", str(memory_root))
    raw = _prepare_raw(memory_root)
    hidden_file = raw / ".DS_Store"
    hidden_file.write_text("metadata")

    summary = auto_sort_memory()

    assert hidden_file.exists()
    assert ".DS_Store" in summary["skipped"]
