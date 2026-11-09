"""Coverage tests for repository-map generation."""

from __future__ import annotations

import sys
from pathlib import Path

from huey.memory.PY import generate_repo_map as repo_map


def test_should_skip_hidden_and_cache_paths(tmp_path: Path) -> None:
    assert repo_map._should_skip(tmp_path / ".hidden")
    assert repo_map._should_skip(tmp_path / "__pycache__")
    assert not repo_map._should_skip(tmp_path / "visible.py")


def test_tree_lines_sorts_children_and_skips_hidden_entries(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "z_dir").mkdir(parents=True)
    (root / "a.py").write_text("", encoding="utf-8")
    (root / ".secret").write_text("", encoding="utf-8")
    (root / "__pycache__").mkdir()

    lines = repo_map._tree_lines(root, max_depth=2)

    assert lines == ["- repo/", "  - a.py", "  - z_dir/"]


def test_tree_lines_respects_depth_and_file_roots(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    nested = root / "src" / "pkg"
    nested.mkdir(parents=True)
    file_path = nested / "module.py"
    file_path.write_text("", encoding="utf-8")

    assert repo_map._tree_lines(root, max_depth=1) == ["- repo/", "  - src/"]
    assert repo_map._tree_lines(root, max_depth=-1) == []
    assert repo_map._tree_lines(file_path, max_depth=3) == ["- module.py"]


def test_build_repository_map_includes_existing_sections_only(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "other").mkdir()
    (tmp_path / "src" / "module.py").write_text("", encoding="utf-8")

    result = repo_map.build_repository_map(tmp_path, max_depth=2)

    assert result.startswith("# Repository Map\n\nGenerated from the current checkout.")
    assert "## src\n\n- src/\n  - module.py" in result
    assert "## tests\n\n- tests/" in result
    assert "## other" not in result


def test_build_repository_map_for_empty_root_has_header(tmp_path: Path) -> None:
    assert repo_map.build_repository_map(tmp_path) == (
        "# Repository Map\n\nGenerated from the current checkout.\n\n"
    )


def test_write_repository_map_creates_parent_and_returns_path(
    tmp_path: Path,
) -> None:
    root = tmp_path / "checkout"
    (root / "scripts").mkdir(parents=True)
    output = tmp_path / "nested" / "map.md"

    written = repo_map.write_repository_map(output, root=root)

    assert written == output
    assert output.read_text(encoding="utf-8") == repo_map.build_repository_map(root)


def test_main_uses_arguments_writes_map_and_reports_path(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = tmp_path / "checkout"
    (root / "docs").mkdir(parents=True)
    output = tmp_path / "generated" / "map.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_repo_map",
            "--root",
            str(root),
            "--output",
            str(output),
            "--max-depth",
            "1",
        ],
    )

    result = repo_map.main()

    assert result == 0
    assert output.is_file()
    assert capsys.readouterr().out == f"Wrote repository map to {output.resolve()}\n"
