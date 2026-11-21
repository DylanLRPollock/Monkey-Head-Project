"""Check the signed pinned 7.3.4 source lock and fail-closed rejected variants."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from huey.kernel_build.models import SourceType
from huey.kernel_build.runner import CommandSpec, RunnerError, RunnerResult
from huey.kernel_build.source_manager import (
    SourceLock,
    SourceLockUnresolvedError,
    SourceManager,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = REPO_ROOT / "kernel" / "huey-linux" / "source.lock.json"
PLACEHOLDER_CHECKSUM = "0" * 64
EXPECTED_SHA = "b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f"


class NeverCalledRunner:
    def __init__(self) -> None:
        self.calls: list[CommandSpec] = []

    def run(self, spec: CommandSpec, *, dry_run: bool = False) -> RunnerResult:
        self.calls.append(spec)
        raise RunnerError("Unresolved source must not trigger a command")


def _unresolved_lock() -> SourceLock:
    """Synthetic unresolved variant, preserving verified repo metadata."""
    return replace(
        SourceLock.load_from_path(LOCK_PATH),
        status="unresolved",
        checksum_sha256=PLACEHOLDER_CHECKSUM,
        retrieved_date=None,
    )


def test_lock_file_exists() -> None:
    assert LOCK_PATH.is_file()


def test_lock_file_is_valid_json() -> None:
    assert isinstance(json.loads(LOCK_PATH.read_text(encoding="utf-8")), dict)


def test_lock_loads_via_source_manager_model() -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    assert lock.schema_version == 1
    assert lock.source_type is SourceType.UPSTREAM
    assert lock.version == "7.3.4"
    assert lock.archive_filename == "linux-7.3.4.tar.xz"


def test_lock_round_trips_through_to_dict() -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    assert SourceLock.from_dict(lock.to_dict()) == lock


def test_source_is_pinned_to_verified_checksum() -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    assert lock.status == "pinned"
    assert lock.checksum_sha256 == EXPECTED_SHA
    assert lock.checksum_sha256 != PLACEHOLDER_CHECKSUM
    assert lock.retrieved_date == "2026-11-15"
    assert lock.origin_url == (
        "https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.3.4.tar.xz"
    )


def test_provenance_preserves_release_signature_information() -> None:
    notes = SourceLock.load_from_path(LOCK_PATH).notes
    assert "signature" in notes.lower()
    assert "647F28654894E3BD457199BE38DBBDC86092693E" in notes


@pytest.mark.parametrize("dry_run", [False, True])
def test_synthetic_unresolved_lock_rejected_before_io(
    tmp_path: Path, dry_run: bool
) -> None:
    mgr = SourceManager(
        NeverCalledRunner(), cache_dir=tmp_path / "c",
        workspace_dir=tmp_path / "w",
    )
    with pytest.raises(SourceLockUnresolvedError):
        mgr.prepare(_unresolved_lock(), dry_run=dry_run)
    assert list(tmp_path.iterdir()) == []


def test_unresolved_source_does_not_invoke_runner(tmp_path: Path) -> None:
    runner = NeverCalledRunner()
    mgr = SourceManager(runner, cache_dir=tmp_path / "c",
                        workspace_dir=tmp_path / "w")
    with pytest.raises(SourceLockUnresolvedError):
        mgr.prepare(_unresolved_lock())
    assert runner.calls == []


def test_status_flip_without_real_checksum_still_fails(tmp_path: Path) -> None:
    mgr = SourceManager(
        NeverCalledRunner(), cache_dir=tmp_path / "c",
        workspace_dir=tmp_path / "w",
    )
    with pytest.raises(SourceLockUnresolvedError, match="verified SHA-256"):
        mgr.prepare(replace(_unresolved_lock(), status="pinned"), allow_network=False)
    assert list(tmp_path.iterdir()) == []


def test_pinned_source_is_plannable_offline_without_side_effects(
    tmp_path: Path,
) -> None:
    runner = NeverCalledRunner()
    mgr = SourceManager(
        runner, cache_dir=tmp_path / "cache",
        workspace_dir=tmp_path / "workspace",
    )
    result = mgr.prepare(
        SourceLock.load_from_path(LOCK_PATH),
        allow_network=False,
        dry_run=True,
    )
    assert result.dry_run is True
    assert result.archive_sha256 == EXPECTED_SHA
    assert runner.calls == []
    assert list(tmp_path.iterdir()) == []
