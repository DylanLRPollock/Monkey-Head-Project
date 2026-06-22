from __future__ import annotations

from pathlib import Path

import pytest

from huey.v1.fixture_registry import FixtureRegistry


def test_register_and_load_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.mp3"
    fixture.write_bytes(b"audio")
    registry = FixtureRegistry(tmp_path / "fixtures.json")
    record = registry.register("known-audio", fixture, notes="test")
    assert record.sha256
    assert registry.get("known-audio").notes == "test"


def test_register_refuses_duplicate_without_overwrite(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.mp3"
    fixture.write_bytes(b"audio")
    registry = FixtureRegistry(tmp_path / "fixtures.json")
    registry.register("known-audio", fixture)
    with pytest.raises(ValueError):
        registry.register("known-audio", fixture)
