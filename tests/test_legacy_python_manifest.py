"""Validate that the full legacy Python inventory remains reconciled."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "src" / "huey" / "memory" / "PY"
MANIFEST = ROOT / "docs" / "development" / "legacy-python-144-disposition.json"


def test_every_original_python_file_has_a_disposition() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = data["items"]
    assert data["schema"] == "huey.legacy_python_disposition.v1"
    assert data["initial_count"] == len(rows) == 144
    assert len({row["name"] for row in rows}) == len(rows)
    assert all(row["legacy_path"].startswith("src/huey/memory/PY/") for row in rows)
    assert all(row["proposed_destination"] for row in rows)
    assert all(row["disposition"] for row in rows)
    assert dict(Counter(row["disposition"] for row in rows)) == data["status_counts"]


def test_remaining_legacy_files_match_inventory() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    remaining = {
        row["legacy_path"] for row in data["items"] if row["retained_in_legacy"]
    }
    actual = {path.relative_to(ROOT).as_posix() for path in LEGACY.glob("*.py")}
    assert actual == remaining
    assert len(actual) == data["retained_after_this_change"]


def test_relocated_tests_and_examples_are_present_without_duplicate_copies() -> None:
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))["items"]
    moved = [
        row
        for row in rows
        if row["disposition"] in {"moved_test_collected", "moved_opt_in_example"}
    ]
    assert len(moved) == 16
    for row in moved:
        destination = ROOT / row["proposed_destination"]
        assert destination.is_file(), row["name"]
        assert not (ROOT / row["legacy_path"]).exists(), row["name"]
        if row["disposition"] == "moved_test_collected":
            assert destination.parent == ROOT / "tests"
            assert destination.name.startswith("test_")


def test_known_promotions_keep_compatibility_modules() -> None:
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))["items"]
    promoted = [row for row in rows if row["disposition"] == "promoted_with_legacy_alias"]
    assert len(promoted) == 11
    for row in promoted:
        assert (ROOT / row["legacy_path"]).is_file()
        assert (ROOT / row["proposed_destination"]).is_file()
