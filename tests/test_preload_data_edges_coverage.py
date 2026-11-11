"""Cover memory preload filtering and command-line output branches."""

from __future__ import annotations

import sys
from pathlib import Path

from huey.memory import preload_data


def test_prompt_loader_handles_missing_and_comment_only_files(monkeypatch, tmp_path):
    monkeypatch.setattr(preload_data, "_PROMPT_CANDIDATES", (tmp_path / "missing.csv",))
    assert preload_data.load_prompts() == []

    comments = tmp_path / "comments.csv"
    comments.write_text("# first comment\n\n# final comment\n", encoding="utf-8")
    monkeypatch.setattr(preload_data, "_PROMPT_CANDIDATES", (comments,))
    assert preload_data.load_prompts() == []


def test_memory_loader_filters_hidden_code_symlinks_and_empty_directories(
    monkeypatch, tmp_path
):
    root = tmp_path / "memory"
    root.mkdir()
    for name in (
        ".hidden",
        "PY",
        "__pycache__",
        ".git",
        ".venv",
        "INDEX",
        "empty",
        "docs",
    ):
        (root / name).mkdir()

    (root / "docs" / "guide.pdf").write_text("data", encoding="utf-8")
    (root / "docs" / "secret.py").write_text("pass", encoding="utf-8")
    (root / "docs" / ".private.pdf").write_text("private", encoding="utf-8")
    outside = tmp_path / "outside.pdf"
    outside.write_text("external", encoding="utf-8")
    (root / "docs" / "linked.pdf").symlink_to(outside)
    (root / "linked-directory").symlink_to(root / "docs", target_is_directory=True)
    monkeypatch.setattr(preload_data, "get_memory_path", lambda *, create: root)

    assert preload_data.load_memory() == {
        "docs": [str((root / "docs" / "guide.pdf").resolve())]
    }


def test_memory_loader_returns_empty_for_missing_root(monkeypatch, tmp_path):
    missing = tmp_path / "missing"
    monkeypatch.setattr(preload_data, "get_memory_path", lambda *, create: missing)
    assert preload_data.load_memory() == {}


def test_preload_cli_prints_summary_and_full_data(monkeypatch, capsys):
    data = {"prompts": [{"name": "one"}], "memory": {"PDF": ["one.pdf", "two.pdf"]}}
    monkeypatch.setattr(preload_data, "preload_all", lambda: data)

    monkeypatch.setattr("sys.argv", ["preload-data", "--summary"])
    preload_data.main()
    assert capsys.readouterr().out == "Prompts loaded: 1\nPDF: 2 files\n"

    monkeypatch.setattr("sys.argv", ["preload-data"])
    preload_data.main()
    assert capsys.readouterr().out == f"{data}\n"


def test_module_entrypoint_runs_as_main(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("MEMORY_PATH", str(tmp_path / "memory"))
    monkeypatch.setattr(sys, "argv", ["preload-data", "--summary"])
    source = Path(preload_data.__file__)

    namespace = {"__name__": "__main__", "__file__": str(source)}
    exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), namespace)

    output = capsys.readouterr().out
    assert output.startswith("Prompts loaded: ")
    assert " files" not in output
