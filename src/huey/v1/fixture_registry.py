"""Registry helpers for V1 proof-loop fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from shutil import copy2

from huey.memory.pipeline.metadata import generate_metadata
from huey.utils.paths import ensure_subdirectory


def _registry_path(path: Path | None = None) -> Path:
    return path or (ensure_subdirectory("V1", "fixtures") / "registry.json")


def _read_registry(path: Path | None = None) -> dict[str, dict[str, object]]:
    registry_path = _registry_path(path)
    if not registry_path.exists():
        return {}
    return json.loads(registry_path.read_text(encoding="utf-8"))


def _write_registry(
    payload: dict[str, dict[str, object]], path: Path | None = None
) -> Path:
    registry_path = _registry_path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return registry_path


def register_fixture(
    source: str | Path,
    *,
    fixture_id: str | None = None,
    description: str = "",
    copy_to_registry: bool = False,
    registry_path: Path | None = None,
) -> dict[str, object]:
    """Register a fixture path in the V1 registry."""

    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    target_path = source_path
    if copy_to_registry:
        fixtures_dir = ensure_subdirectory("V1", "fixtures")
        target_path = fixtures_dir / source_path.name
        copy2(source_path, target_path)
    key = fixture_id or source_path.stem
    entry = {
        "id": key,
        "path": str(target_path),
        "description": description or f"Fixture for {source_path.name}",
        "metadata": generate_metadata(target_path),
    }
    payload = _read_registry(registry_path)
    payload[key] = entry
    _write_registry(payload, registry_path)
    return entry


def load_fixture(
    fixture_id: str, *, registry_path: Path | None = None
) -> dict[str, object]:
    """Return fixture metadata from the registry."""

    payload = _read_registry(registry_path)
    if fixture_id not in payload:
        raise KeyError(f"Unknown fixture id: {fixture_id}")
    return payload[fixture_id]


def list_fixtures(*, registry_path: Path | None = None) -> list[dict[str, object]]:
    """List every registered V1 fixture."""

    payload = _read_registry(registry_path)
    return [payload[key] for key in sorted(payload)]


__all__ = ["list_fixtures", "load_fixture", "register_fixture"]
