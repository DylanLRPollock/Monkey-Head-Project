"""Exercise legacy temp-file and remover helpers even when optional tests skip."""

from __future__ import annotations

import importlib
import runpy
import sys
from pathlib import Path

import pytest


def test_manage_temp_files_delete_archive_and_validation(tmp_path, capsys):
    module = importlib.import_module("huey.memory.PY.huey_disk_manager_temp")
    missing = tmp_path / "missing"
    with pytest.raises(FileNotFoundError, match="not found"):
        module.manage_temp_files(str(missing), "delete")

    temp = tmp_path / "scratch"
    temp.mkdir()
    (temp / "payload.txt").write_text("discard", encoding="utf-8")
    with pytest.raises(ValueError, match=r"delete.*archive"):
        module.manage_temp_files(str(temp), "invalid")

    module.manage_temp_files(str(temp), "delete")
    assert temp.is_dir() and list(temp.iterdir()) == []
    assert "deleted" in capsys.readouterr().out

    (temp / "keep.txt").write_text("archive", encoding="utf-8")
    module.manage_temp_files(str(temp), "archive")
    assert temp.is_dir() and (tmp_path / "scratch_archive" / "keep.txt").is_file()
    assert "archived" in capsys.readouterr().out


def test_temp_file_os_errors_are_wrapped(tmp_path, monkeypatch):
    module = importlib.import_module("huey.memory.PY.huey_disk_manager_temp")
    temp = tmp_path / "scratch"
    temp.mkdir()

    def fail(*_args, **_kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(module.shutil, "rmtree", fail)
    with pytest.raises(OSError, match=r"Error managing temporary files.*denied"):
        module.manage_temp_files(str(temp), "delete")


def test_remove_files_dry_run_delete_empty_and_errors(tmp_path, monkeypatch, capsys):
    module = importlib.import_module("huey.memory.PY.huey_remover")
    with pytest.raises(FileNotFoundError, match="not found"):
        module.remove_files(tmp_path / "missing", ".txt")

    target = tmp_path / "notes.txt"
    other = tmp_path / "notes.log"
    target.write_text("text", encoding="utf-8")
    other.write_text("log", encoding="utf-8")
    planned = module.remove_files(tmp_path, ".txt", dry_run=True)
    assert planned == [str(target)]
    assert target.exists()
    assert "dry-run" in capsys.readouterr().out
    assert module.remove_files(tmp_path, ".missing") == []
    assert module.remove_files(tmp_path, ".txt") == [str(target)]
    assert not target.exists() and other.exists()
    assert "Removed file" in capsys.readouterr().out

    monkeypatch.setattr(
        module.os, "remove", lambda _path: (_ for _ in ()).throw(OSError("denied"))
    )
    target.write_text("text", encoding="utf-8")
    with pytest.raises(OSError, match=r"Error removing files.*denied"):
        module.remove_files(tmp_path, ".txt")

    monkeypatch.setattr(
        module.os, "listdir", lambda _path: (_ for _ in ()).throw(OSError("no list"))
    )
    with pytest.raises(OSError, match=r"Error removing files.*no list"):
        module.remove_files(tmp_path, ".txt")


def test_legacy_command_line_entrypoints(tmp_path, monkeypatch, capsys):
    root = Path(__file__).resolve().parents[1] / "src/huey/memory/PY"
    temp_main = root / "huey_disk_manager_temp.py"
    remove_main = root / "huey_remover.py"

    archive = tmp_path / "cli-temp"
    archive.mkdir()
    (archive / "file.txt").write_text("cli", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [str(temp_main), str(archive), "archive"])
    runpy.run_path(str(temp_main), run_name="__main__")
    assert (tmp_path / "cli-temp_archive" / "file.txt").is_file()
    assert "archived" in capsys.readouterr().out

    file = tmp_path / "remove.txt"
    file.write_text("cli", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [str(remove_main), str(tmp_path), ".txt"])
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    with pytest.raises(SystemExit) as cancelled:
        runpy.run_path(str(remove_main), run_name="__main__")
    assert cancelled.value.code == 1
    assert file.exists()
    assert "Cancelled" in capsys.readouterr().out

    monkeypatch.setattr(
        sys, "argv", [str(remove_main), str(tmp_path), ".txt", "--dry-run"]
    )
    runpy.run_path(str(remove_main), run_name="__main__")
    assert file.exists()
    assert "dry-run" in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", [str(remove_main), str(tmp_path), ".txt", "--yes"])
    runpy.run_path(str(remove_main), run_name="__main__")
    assert not file.exists()
