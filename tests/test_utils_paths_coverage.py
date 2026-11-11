"""Exercise memory-directory selection and deduplication boundaries."""

from __future__ import annotations

import pytest

from huey.utils import paths


def test_expand_path_resolves_relative_values_and_keeps_absolute_paths(
    tmp_path, monkeypatch
):
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setattr(paths, "_PROJECT_ROOT", root)
    absolute = tmp_path / "absolute-memory"
    assert paths._expand_path(str(absolute)) == absolute
    assert paths._expand_path("relative/memory") == (root / "relative/memory").resolve()


def test_memory_path_rejects_file_override_and_supports_create_false(
    tmp_path, monkeypatch
):
    file_path = tmp_path / "memory-file"
    file_path.write_text("x", encoding="utf-8")
    monkeypatch.setenv("MEMORY_PATH", str(file_path))
    with pytest.raises(NotADirectoryError, match="MEMORY_PATH is not a directory"):
        paths.get_memory_path()

    target = tmp_path / "not-created"
    monkeypatch.setenv("MEMORY_PATH", str(target))
    assert paths.get_memory_path(create=False) == target
    assert not target.exists()


def test_memory_path_creates_preferred_fallback_when_no_locations_exist(
    monkeypatch, tmp_path
):
    project = tmp_path / "new-project"
    source = project / "src"
    monkeypatch.setattr(paths, "_PROJECT_ROOT", project)
    monkeypatch.setattr(paths, "_SRC_ROOT", source)
    monkeypatch.delenv("MEMORY_PATH", raising=False)
    result = paths.get_memory_path(create=True)
    assert result == project / "memory"
    assert result.is_dir()


def test_default_memory_path_selects_preferred_packaged_and_missing_fallbacks(
    monkeypatch, tmp_path
):
    project = tmp_path / "project"
    source = project / "src"
    packaged = source / "huey" / "memory"
    project.mkdir()
    source.mkdir()
    monkeypatch.setattr(paths, "_PROJECT_ROOT", project)
    monkeypatch.setattr(paths, "_SRC_ROOT", source)
    monkeypatch.delenv("MEMORY_PATH", raising=False)

    assert paths.get_memory_path(create=False) == project / "memory"
    packaged.mkdir(parents=True)
    assert paths.get_memory_path(create=False) == packaged
    assert paths.get_memory_path(create=True) == packaged

    preferred = project / "memory"
    preferred.mkdir()
    assert paths.get_memory_path(create=False) == preferred
    monkeypatch.setattr(paths, "_SRC_ROOT", tmp_path / "empty-src")
    (packaged).rmdir()
    assert paths.get_memory_path(create=False) == preferred


def test_memory_candidates_include_extra_and_deduplicate_resolved_paths(
    monkeypatch, tmp_path
):
    project = tmp_path / "project"
    source = project / "src"
    preferred = project / "memory"
    packaged = source / "huey" / "memory"
    preferred.mkdir(parents=True)
    packaged.mkdir(parents=True)
    relative = tmp_path / "alias"
    relative.symlink_to(preferred, target_is_directory=True)
    monkeypatch.setattr(paths, "_PROJECT_ROOT", project)
    monkeypatch.setattr(paths, "_SRC_ROOT", source)
    monkeypatch.setenv("MEMORY_PATH", str(relative))

    candidates = paths.memory_candidates([preferred, tmp_path / "extra"])
    assert candidates == [
        relative.resolve(),
        packaged.resolve(),
        (tmp_path / "extra").resolve(),
    ]


def test_log_directory_and_nested_paths_are_created_from_override(
    tmp_path, monkeypatch
):
    base = tmp_path / "memory"
    monkeypatch.setenv("MEMORY_PATH", str(base))
    target = paths.ensure_subdirectory("AUDIO", "prepared")
    logs = paths.get_logs_dir()
    assert target == base / "AUDIO" / "prepared"
    assert target.is_dir()
    assert logs == base / "LOGS"
    assert logs.is_dir()
