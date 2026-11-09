"""Tests for command-center workspace JSON storage."""

from __future__ import annotations

import json

import pytest

from huey.gui import storage


def test_default_workspace_path_uses_gui_subdirectory(tmp_path, monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        storage,
        "ensure_subdirectory",
        lambda *parts: calls.append(parts) or tmp_path,
    )

    result = storage.default_workspace_path()

    assert calls == [("GUI",)]
    assert result == tmp_path / "command-center-workspace.json"


def test_load_workspace_returns_default_data_when_file_is_missing(tmp_path) -> None:
    result = storage.load_workspace(tmp_path / "missing.json")

    assert isinstance(result, storage.WorkspaceData)
    assert result.repositories
    assert result.phases
    assert result.validation_commands
    assert result.operator_panel
    assert result.notes == ""
    assert result.version == "0.1.0"


def test_load_workspace_uses_default_path_when_path_is_omitted(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "workspace.json"
    monkeypatch.setattr(storage, "default_workspace_path", lambda: path)

    result = storage.load_workspace()

    assert result.repositories
    assert path == tmp_path / "workspace.json"
    assert not path.exists()


def test_import_workspace_fills_missing_fields_from_defaults() -> None:
    result = storage.import_workspace(json.dumps({"notes": 12, "version": 3}))

    assert isinstance(result, storage.WorkspaceData)
    assert result.repositories
    assert result.phases
    assert result.validation_commands
    assert result.operator_panel
    assert result.notes == "12"
    assert result.version == "3"


def test_export_and_import_workspace_round_trip() -> None:
    original = storage.WorkspaceData(
        repositories=[{"name": "repo", "path": "/tmp/repo"}],
        phases=[{"name": "phase", "complete": False}],
        validation_commands=[{"command": "python -m pytest"}],
        operator_panel={"expanded": True},
        notes="keep this note",
        version="2.0",
    )

    encoded = storage.export_workspace(original)
    payload = json.loads(encoded)
    restored = storage.import_workspace(encoded)

    assert payload["notes"] == "keep this note"
    assert list(payload) == sorted(payload)
    assert restored == original


def test_save_workspace_creates_parent_and_uses_default_path(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "nested" / "workspace.json"
    monkeypatch.setattr(storage, "default_workspace_path", lambda: path)
    data = storage.WorkspaceData(
        repositories=[],
        phases=[],
        validation_commands=[],
        operator_panel={},
        notes="saved",
    )

    saved_path = storage.save_workspace(data)

    assert saved_path == path
    assert path.exists()
    saved_text = path.read_text(encoding="utf-8")
    restored = storage.import_workspace(saved_text)
    assert restored == data


def test_load_workspace_reads_existing_json(tmp_path) -> None:
    path = tmp_path / "workspace.json"
    data = storage.WorkspaceData(
        repositories=[],
        phases=[],
        validation_commands=[],
        operator_panel={"compact": True},
        notes="loaded",
    )
    encoded = storage.export_workspace(data)
    path.write_text(encoded, encoding="utf-8")

    loaded = storage.load_workspace(path)

    assert loaded == data


def test_load_workspace_propagates_invalid_json(tmp_path) -> None:
    path = tmp_path / "workspace.json"
    path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        storage.load_workspace(path)


def test_reset_workspace_writes_and_returns_defaults(tmp_path, monkeypatch) -> None:
    path = tmp_path / "workspace.json"
    monkeypatch.setattr(storage, "default_workspace_path", lambda: path)

    result = storage.reset_workspace()

    assert isinstance(result, storage.WorkspaceData)
    assert path.exists()
    saved_text = path.read_text(encoding="utf-8")
    restored = storage.import_workspace(saved_text)
    assert restored == result
