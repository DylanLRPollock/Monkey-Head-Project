"""Cover data-loading helpers without requiring the optional TensorFlow stack."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture
def feed_module(monkeypatch):
    package = "huey.memory.PY"
    module_name = f"{package}._coverage_tensorflow_feed"
    trainer = ModuleType(f"{package}.chat_learning")
    trainer.train_from_chat_and_pdfs = lambda *_args, **_kwargs: None
    monkeypatch.setitem(sys.modules, trainer.__name__, trainer)
    source = (
        Path(__file__).resolve().parents[1] / "src/huey/memory/PY/tensorflow_feed.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    return module


def test_load_logs_reads_only_supported_top_level_files(feed_module, tmp_path):
    (tmp_path / "one.txt").write_text("plain", encoding="utf-8")
    (tmp_path / "two.log").write_text("log", encoding="utf-8")
    (tmp_path / "ignore.csv").write_text("skip", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "deep.txt").write_text("nested", encoding="utf-8")
    (tmp_path / "invalid.txt").write_bytes(b"\xff")
    assert set(feed_module.load_logs(tmp_path)) == {"plain", "log"}


def test_prompt_and_memory_loaders_handle_nested_and_invalid_files(
    feed_module, tmp_path, monkeypatch, caplog
):
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "nested").mkdir()
    (prompts / "readme.txt").write_text("prompt", encoding="utf-8")
    (prompts / "table.csv").write_text("first,second\nthird,fourth\n", encoding="utf-8")
    (prompts / "ignore.md").write_text("ignored", encoding="utf-8")
    (prompts / "invalid.txt").write_bytes(b"\xff")
    (prompts / "bad.csv").write_text("bad", encoding="utf-8")

    original_open = Path.open

    def open_with_bad_csv(path, *args, **kwargs):
        if path.name == "bad.csv":
            raise csv.Error("bad csv")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", open_with_bad_csv)
    with caplog.at_level("DEBUG"):
        assert set(feed_module.load_prompts(prompts)) == {
            "prompt",
            "first",
            "second",
            "third",
            "fourth",
        }
    assert "Failed to read text file" in caplog.text
    assert "Failed to read CSV file" in caplog.text

    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "good.json").write_text('{"answer": 42}', encoding="utf-8")
    (memory / "bad.json").write_text("{broken", encoding="utf-8")
    (memory / "invalid.json").write_bytes(b"\xff")
    (memory / "unreadable.json").write_text("{}", encoding="utf-8")
    original_read_text = Path.read_text

    def read_with_error(path, *args, **kwargs):
        if path.name == "unreadable.json":
            raise PermissionError("denied")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_with_error)
    with caplog.at_level("WARNING"):
        assert feed_module.load_memory_texts(memory) == ['{"answer": 42}']
    assert "Failed to load JSON" in caplog.text


def test_train_from_project_sources_aggregates_inputs_and_forwards_epochs(
    feed_module, tmp_path, monkeypatch
):
    logs = tmp_path / "logs"
    prompts = tmp_path / "prompts"
    memory = tmp_path / "memory"
    logs.mkdir()
    prompts.mkdir()
    memory.mkdir()
    (logs / "conversation.log").write_text("logged", encoding="utf-8")
    (prompts / "prompt.txt").write_text("prompted", encoding="utf-8")
    (memory / "facts.json").write_text(json.dumps({"fact": 1}), encoding="utf-8")
    (memory / "paper.pdf").write_bytes(b"pdf")
    observed = {}
    sentinel = object()

    def train(chats, pdfs, *, epochs):
        observed.update(chats=chats, pdfs=pdfs, epochs=epochs)
        return sentinel

    monkeypatch.setattr(feed_module, "train_from_chat_and_pdfs", train)
    result = feed_module.train_from_project_sources(logs, prompts, memory, epochs=3)
    assert result is sentinel
    assert observed == {
        "chats": ["logged", "prompted", '{"fact": 1}'],
        "pdfs": [str(memory / "paper.pdf")],
        "epochs": 3,
    }
