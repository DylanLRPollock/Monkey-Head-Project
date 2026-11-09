"""Coverage tests for the memory storage manager and its CLI."""

from __future__ import annotations

import os
import time
from pathlib import Path

from huey.memory.PY import storage_management as storage


def test_manager_uses_memory_dir_and_creates_default_structure(
    tmp_path, monkeypatch
) -> None:
    base = tmp_path / "memory"
    monkeypatch.setenv("MEMORY_DIR", str(base))

    manager = storage.StorageManager()

    assert manager.base_dir == base
    assert {path.name for path in base.iterdir()} == set(storage.DEFAULT_FOLDERS)


def test_unique_move_appends_counter_when_destination_names_conflict(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    destination_dir = tmp_path / "destination"
    source_dir.mkdir()
    destination_dir.mkdir()
    source = source_dir / "report.txt"
    source.write_text("new", encoding="utf-8")
    (destination_dir / "report.txt").write_text("existing", encoding="utf-8")
    (destination_dir / "report_1.txt").write_text("also existing", encoding="utf-8")

    manager = storage.StorageManager(tmp_path / "memory")
    moved = manager._unique_move(source, destination_dir)

    assert moved == destination_dir / "report_2.txt"
    assert moved.read_text(encoding="utf-8") == "new"
    assert (destination_dir / "report.txt").read_text(encoding="utf-8") == "existing"
    assert not source.exists()


def test_sort_root_files_dry_run_and_route_extensions(tmp_path: Path) -> None:
    base = tmp_path / "memory"
    manager = storage.StorageManager(base)
    pdf = base / "report.PDF"
    unknown = base / "blob.bin"
    no_extension = base / "README"
    nested = base / "nested"
    pdf.write_text("pdf", encoding="utf-8")
    unknown.write_text("binary", encoding="utf-8")
    no_extension.write_text("text", encoding="utf-8")
    nested.mkdir()

    manager.sort_root_files(dry_run=True)

    assert pdf.exists()
    assert unknown.exists()
    assert no_extension.exists()

    manager.sort_root_files()

    assert (base / "PDF" / "report.PDF").is_file()
    assert (base / "BIN" / "blob.bin").is_file()
    assert (base / "MISC" / "README").is_file()
    assert nested.is_dir()


def test_list_files_sorts_results_and_handles_missing_folder(tmp_path: Path) -> None:
    base = tmp_path / "memory"
    folder = base / "TXT"
    folder.mkdir(parents=True)
    (folder / "z.txt").write_text("z", encoding="utf-8")
    (folder / "a.txt").write_text("a", encoding="utf-8")
    manager = storage.StorageManager(base)

    assert manager.list_files("TXT") == [
        str(folder / "a.txt"),
        str(folder / "z.txt"),
    ]
    assert manager.list_files("missing") == []


def test_cleanup_empty_dirs_preserves_directories_with_files(tmp_path: Path) -> None:
    base = tmp_path / "memory"
    empty = base / "EMPTY"
    populated = base / "POPULATED"
    empty.mkdir(parents=True)
    populated.mkdir()
    (populated / "keep.txt").write_text("keep", encoding="utf-8")
    manager = storage.StorageManager(base)

    manager.cleanup_empty_dirs()

    assert not empty.exists()
    assert populated.is_dir()
    assert (populated / "keep.txt").exists()


def test_get_total_size_scopes_results_and_handles_missing_paths(
    tmp_path: Path,
) -> None:
    base = tmp_path / "memory"
    folder = base / "TXT"
    folder.mkdir(parents=True)
    (folder / "a.txt").write_bytes(b"1234")
    (folder / "b.txt").write_bytes(b"567")
    manager = storage.StorageManager(base)

    assert manager.get_total_size("TXT") == 7
    assert manager.get_total_size("missing") == 0


def test_get_total_size_skips_files_that_cannot_be_statted(
    tmp_path: Path, monkeypatch, caplog
) -> None:
    base = tmp_path / "memory"
    base.mkdir()
    readable = base / "readable.bin"
    blocked = base / "blocked.bin"
    readable.write_bytes(b"ok")
    blocked.write_bytes(b"no")
    manager = storage.StorageManager(base)
    original_is_file = Path.is_file
    original_stat = Path.stat

    def selective_is_file(path: Path) -> bool:
        return True if path == blocked else original_is_file(path)

    def selective_stat(path: Path, *args, **kwargs):
        if path == blocked:
            raise PermissionError("blocked")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "is_file", selective_is_file)
    monkeypatch.setattr(Path, "stat", selective_stat)
    caplog.set_level("WARNING")

    total = manager.get_total_size()

    assert total == 2
    assert "Failed to stat file for size calculation" in caplog.text
    assert "blocked.bin" in caplog.text


def test_remove_older_than_dry_run_then_deletes_only_stale_files(
    tmp_path: Path, monkeypatch
) -> None:
    base = tmp_path / "memory"
    archive = base / "ARCHIVE"
    archive.mkdir(parents=True)
    stale = archive / "stale.txt"
    recent = archive / "recent.txt"
    stale.write_text("stale", encoding="utf-8")
    recent.write_text("recent", encoding="utf-8")
    now = time.time()
    old_time = now - 30 * 86400
    recent_time = now - 1 * 86400
    os.utime(stale, (old_time, old_time))
    os.utime(recent, (recent_time, recent_time))
    manager = storage.StorageManager(base)
    monkeypatch.setattr(storage.time, "time", lambda: now)

    preview_count = manager.remove_older_than(7, "ARCHIVE", dry_run=True)

    assert preview_count == 1
    assert stale.exists()
    assert recent.exists()

    removed_count = manager.remove_older_than(7, "ARCHIVE")

    assert removed_count == 1
    assert not stale.exists()
    assert recent.exists()


def test_remove_older_than_returns_zero_for_invalid_age_or_missing_folder(
    tmp_path: Path,
) -> None:
    manager = storage.StorageManager(tmp_path / "memory")

    assert manager.remove_older_than(0) == 0
    assert manager.remove_older_than(-2) == 0
    assert manager.remove_older_than(7, "missing") == 0


def test_remove_older_than_logs_inspection_and_stat_errors(
    tmp_path: Path, monkeypatch, caplog
) -> None:
    base = tmp_path / "memory"
    base.mkdir()
    cannot_inspect = base / "cannot-inspect.txt"
    cannot_stat = base / "cannot-stat.txt"
    cannot_inspect.write_text("inspect", encoding="utf-8")
    cannot_stat.write_text("stat", encoding="utf-8")
    old_time = time.time() - 30 * 86400
    os.utime(cannot_inspect, (old_time, old_time))
    os.utime(cannot_stat, (old_time, old_time))
    manager = storage.StorageManager(base)
    original_is_file = Path.is_file
    original_stat = Path.stat

    def selective_is_file(path: Path) -> bool:
        if path == cannot_inspect:
            raise OSError("cannot inspect")
        if path == cannot_stat:
            return True
        return original_is_file(path)

    def selective_stat(path: Path, *args, **kwargs):
        if path == cannot_stat:
            raise PermissionError("cannot stat")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "is_file", selective_is_file)
    monkeypatch.setattr(Path, "stat", selective_stat)
    monkeypatch.setattr(storage.time, "time", lambda: time.time() + 60)
    caplog.set_level("WARNING")

    removed = manager.remove_older_than(7)

    assert removed == 0
    assert cannot_inspect.exists()
    assert cannot_stat.exists()
    assert "Failed to inspect path while pruning old files" in caplog.text
    assert "Failed to stat file while pruning old files" in caplog.text


def test_main_sorts_lists_sizes_and_cleans_the_requested_directory(
    tmp_path: Path, capsys
) -> None:
    base = tmp_path / "memory"
    base.mkdir()
    (base / "z.txt").write_text("zz", encoding="utf-8")
    (base / "a.txt").write_text("a", encoding="utf-8")

    storage.main(
        [
            "--path",
            str(base),
            "--sort",
            "--list",
            "TXT",
            "--size",
            "TXT",
            "--cleanup",
        ]
    )

    assert capsys.readouterr().out.splitlines() == [
        str(base / "TXT" / "a.txt"),
        str(base / "TXT" / "z.txt"),
        "3",
    ]


def test_main_prune_confirmation_cancel_dry_run_and_yes_paths(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    base = tmp_path / "memory"
    base.mkdir()
    stale = base / "stale.txt"
    stale.write_text("stale", encoding="utf-8")
    old_time = time.time() - 30 * 86400
    os.utime(stale, (old_time, old_time))
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")

    storage.main(["--path", str(base), "--prune", "7"])

    assert capsys.readouterr().out == "Cancelled.\n"
    assert stale.exists()

    storage.main(["--path", str(base), "--prune", "7", "--dry-run"])

    assert capsys.readouterr().out == "1\n"
    assert stale.exists()

    storage.main(["--path", str(base), "--prune", "7", "--yes"])

    assert capsys.readouterr().out == "1\n"
    assert not stale.exists()
