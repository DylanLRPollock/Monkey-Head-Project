"""Registry helpers for V1 proof-loop fixtures."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from shutil import copy2

from huey.memory.metadata import file_hash, generate_metadata
from huey.utils.paths import ensure_subdirectory, get_memory_path


def _registry_path(path: Path | None = None, *, create: bool = False) -> Path:
    if path is not None:
        return Path(path)
    if create:
        return ensure_subdirectory("V1", "fixtures") / "registry.json"
    return get_memory_path(create=False) / "V1" / "fixtures" / "registry.json"


def _read_registry(path: Path | None = None) -> dict[str, dict[str, object]]:
    registry_path = _registry_path(path)
    if not registry_path.exists():
        return {}
    records = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(records, dict) or not all(
        isinstance(key, str) and isinstance(value, dict)
        for key, value in records.items()
    ):
        raise ValueError(f"Malformed V1 fixture registry: {registry_path}")
    return records


def _write_registry(
    payload: dict[str, dict[str, object]], path: Path | None = None
) -> Path:
    registry_path = _registry_path(path, create=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=registry_path.parent,
            prefix=f".{registry_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, registry_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return registry_path


def register_fixture(
    source: str | Path,
    *,
    fixture_id: str | None = None,
    description: str = "",
    copy_to_registry: bool = False,
    registry_path: Path | None = None,
    overwrite: bool = False,
) -> dict[str, object]:
    """Register a fixture path in the V1 registry."""

    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    key = fixture_id if fixture_id is not None else source_path.stem
    if not isinstance(key, str) or not key.strip():
        raise ValueError("fixture_id must be a nonempty string")
    payload = _read_registry(registry_path)
    if key in payload and not overwrite:
        raise ValueError(f"Fixture id already registered: {key}")

    target_path = source_path
    if copy_to_registry:
        fixtures_dir = ensure_subdirectory("V1", "fixtures")
        target_path = fixtures_dir / source_path.name
        if target_path.is_symlink():
            raise FileExistsError(f"Fixture destination is a symlink: {target_path}")
        if source_path != target_path:
            if target_path.exists():
                if not target_path.is_file() or file_hash(target_path) != file_hash(
                    source_path
                ):
                    raise FileExistsError(
                        f"Different fixture already stored at {target_path}"
                    )
            else:
                copy2(source_path, target_path)
    entry = {
        "id": key,
        "path": str(target_path),
        "description": description or f"Fixture for {source_path.name}",
        "metadata": generate_metadata(target_path),
    }
    payload[key] = entry
    _write_registry(payload, registry_path)
    return entry


def verify_fixture(entry: dict[str, object]) -> bool:
    """Verify that a registered fixture still exists with its original bytes."""
    source = Path(str(entry["path"])).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Registered fixture is missing: {source}")
    metadata = entry.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("Fixture has no integrity metadata")
    expected = metadata.get("sha256")
    size = metadata.get("size_bytes")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("Fixture SHA-256 metadata is missing or malformed")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise ValueError("Fixture size metadata is missing or malformed")
    if source.stat().st_size != size or file_hash(source) != expected:
        raise ValueError(f"Fixture integrity check failed: {source}")
    return True


def load_fixture(
    fixture_id: str, *, registry_path: Path | None = None, verify: bool = True
) -> dict[str, object]:
    """Return registered fixture, verifying its content by default."""
    payload = _read_registry(registry_path)
    if fixture_id not in payload:
        raise KeyError(f"Unknown fixture id: {fixture_id}")
    entry = payload[fixture_id]
    if verify:
        verify_fixture(entry)
    return entry


def list_fixtures(*, registry_path: Path | None = None) -> list[dict[str, object]]:
    """List every registered V1 fixture."""

    payload = _read_registry(registry_path)
    return [payload[key] for key in sorted(payload)]


__all__ = ["list_fixtures", "load_fixture", "register_fixture", "verify_fixture"]
