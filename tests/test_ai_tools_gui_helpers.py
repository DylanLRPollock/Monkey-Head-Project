"""Test pure system and upload helpers used by the optional Tk AI console."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from huey.memory.PY import ai_tools_gui


def test_format_bytes_covers_units_and_none():
    assert ai_tools_gui._format_bytes(None) == "Unknown"
    assert ai_tools_gui._format_bytes(12) == "12.00 B"
    assert ai_tools_gui._format_bytes(1024) == "1.00 KB"
    assert ai_tools_gui._format_bytes(1024**2) == "1.00 MB"
    assert ai_tools_gui._format_bytes(1024**3) == "1.00 GB"
    assert ai_tools_gui._format_bytes(1024**4) == "1.00 TB"
    assert ai_tools_gui._format_bytes(1024**5) == "1.00 PB"


def test_list_memory_uploads_formats_nested_files_and_empty_or_error(
    tmp_path, monkeypatch
):
    uploads = tmp_path / "uploads"
    (uploads / "nested").mkdir(parents=True)
    (uploads / "first.txt").write_text("one")
    (uploads / "nested" / "second.bin").write_bytes(b"12345")
    assert ai_tools_gui._list_memory_uploads(uploads) == [
        "first.txt (3.00 B)",
        "nested/second.bin (5.00 B)",
    ]
    assert ai_tools_gui._list_memory_uploads(tmp_path / "empty") == [
        "No uploaded files yet"
    ]

    class BrokenDirectory:
        def glob(self, _pattern):
            raise PermissionError("denied")

    assert ai_tools_gui._list_memory_uploads(BrokenDirectory()) == [
        "Unable to read uploads directory"
    ]


def test_gather_system_status_without_psutil_and_with_disk_failure(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(ai_tools_gui, "psutil", None)
    monkeypatch.setattr(
        ai_tools_gui.platform,
        "uname",
        lambda: SimpleNamespace(system="TestOS", release="1"),
    )
    monkeypatch.setattr(ai_tools_gui.socket, "gethostname", lambda: "test-host")
    monkeypatch.setattr(ai_tools_gui.platform, "python_version", lambda: "3.x")
    monkeypatch.setattr(
        ai_tools_gui.shutil,
        "disk_usage",
        lambda _path: SimpleNamespace(used=2048, total=4096),
    )
    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "doc.txt").write_bytes(b"123")
    (memory / "nested").mkdir()
    (memory / "nested" / "index.bin").write_bytes(b"4567")
    monkeypatch.setattr(ai_tools_gui, "get_memory_path", lambda create: memory)

    status = ai_tools_gui._gather_system_status()
    assert status["hostname"] == "test-host"
    assert status["system"] == "TestOS"
    assert status["cpu"] == "psutil not installed"
    assert status["memory"] == "psutil not installed"
    assert status["disk"] == "2.00 KB used / 4.00 KB"
    assert status["memory_dir_size"] == "7.00 B"

    monkeypatch.setattr(
        ai_tools_gui.shutil,
        "disk_usage",
        lambda _path: (_ for _ in ()).throw(OSError("unavailable")),
    )
    assert ai_tools_gui._gather_system_status()["disk"] == "Unavailable"


def test_gather_system_status_formats_metrics_and_tolerates_metric_failures(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        ai_tools_gui.platform,
        "uname",
        lambda: SimpleNamespace(system="Linux", release="6"),
    )
    monkeypatch.setattr(ai_tools_gui.platform, "python_version", lambda: "3.13")
    monkeypatch.setattr(ai_tools_gui.socket, "gethostname", lambda: "huey")
    monkeypatch.setattr(ai_tools_gui.shutil, "disk_usage", lambda _path: 1 / 0)
    monkeypatch.setattr(ai_tools_gui, "get_memory_path", lambda create: tmp_path)
    monkeypatch.setattr(ai_tools_gui.time, "time", lambda: 100_000)
    monkeypatch.setattr(
        ai_tools_gui,
        "psutil",
        SimpleNamespace(
            cpu_percent=lambda **_kwargs: 12.34,
            virtual_memory=lambda: SimpleNamespace(used=25, total=100),
            boot_time=lambda: 50_000,
        ),
    )
    status = ai_tools_gui._gather_system_status()
    assert status["cpu"] == "12.3%"
    assert status["memory"] == "25.00 B used / 100.00 B"
    assert status["memory_percent"] == "25.0"
    assert status["uptime"] == "13h 53m"
    assert status["disk"] == "Unavailable"

    monkeypatch.setattr(
        ai_tools_gui,
        "psutil",
        SimpleNamespace(
            cpu_percent=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError()),
            virtual_memory=lambda: (_ for _ in ()).throw(RuntimeError()),
            boot_time=lambda: (_ for _ in ()).throw(RuntimeError()),
        ),
    )
    failed = ai_tools_gui._gather_system_status()
    assert failed["cpu"] == "Unavailable"
    assert failed["memory"] == "Unavailable"
    assert "uptime" not in failed


def test_ai_console_reports_missing_tkinter(monkeypatch):
    monkeypatch.setattr(ai_tools_gui, "tk", None)
    with pytest.raises(RuntimeError, match="tkinter is not available"):
        ai_tools_gui.run_ai_tools()
