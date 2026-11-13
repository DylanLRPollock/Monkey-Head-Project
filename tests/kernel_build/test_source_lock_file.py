"""Offline checks for the unresolved source lock checked into HueyOS (Step 9).

The source lock is intentionally unresolved; both real and dry-run prepare()
refuse it before any cache, workspace, or runner action.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from huey.kernel_build.models import SourceType
from huey.kernel_build.runner import CommandSpec, RunnerError, RunnerResult
from huey.kernel_build.source_manager import (
    SourceLock, SourceLockUnresolvedError, SourceManager,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = REPO_ROOT / "kernel" / "huey-linux" / "source.lock.json"
PLACEHOLDER_CHECKSUM = "0" * 64


class NeverCalledRunner:
    def __init__(self) -> None:
        self.calls: list[CommandSpec] = []

    def run(self, spec: CommandSpec, *, dry_run: bool = False) -> RunnerResult:
        self.calls.append(spec)
        raise RunnerError("No command should run for an unresolved source lock")


def test_lock_file_exists() -> None:
    assert LOCK_PATH.is_file()


def test_lock_file_is_valid_json() -> None:
    assert isinstance(json.loads(LOCK_PATH.read_text(encoding="utf-8")), dict)


def test_lock_contains_unresolved_marker_in_text() -> None:
    assert '"unresolved"' in LOCK_PATH.read_text(encoding="utf-8")


def test_lock_loads_via_source_manager_model() -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    assert lock.schema_version == 1
    assert lock.source_type is SourceType.DEBIAN_LINUX_SOURCE


def test_lock_round_trips_through_to_dict() -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    assert SourceLock.from_dict(lock.to_dict()) == lock


def test_status_and_checksum_correlate() -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    assert lock.status in {"unresolved", "pinned"}
    if lock.status == "unresolved":
        assert lock.checksum_sha256 == PLACEHOLDER_CHECKSUM
    else:
        assert lock.checksum_sha256 != PLACEHOLDER_CHECKSUM


def test_status_and_retrieved_date_correlate() -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    if lock.status == "unresolved":
        assert lock.retrieved_date is None


def test_pinned_lock_has_real_https_url() -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    if lock.status == "pinned":
        assert lock.origin_url.startswith("https://")


def test_prepare_raises_source_lock_unresolved_error(tmp_path: Path) -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    mgr = SourceManager(NeverCalledRunner(), cache_dir=tmp_path/"c", workspace_dir=tmp_path/"w")
    with pytest.raises(SourceLockUnresolvedError):
        mgr.prepare(lock)


def test_prepare_rejection_does_not_invoke_runner(tmp_path: Path) -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    runner = NeverCalledRunner()
    mgr = SourceManager(runner, cache_dir=tmp_path/"c", workspace_dir=tmp_path/"w")
    with pytest.raises(SourceLockUnresolvedError):
        mgr.prepare(lock)
    assert runner.calls == []


def test_prepare_rejection_does_not_touch_filesystem(tmp_path: Path) -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    mgr = SourceManager(NeverCalledRunner(), cache_dir=tmp_path/"c", workspace_dir=tmp_path/"w")
    with pytest.raises(SourceLockUnresolvedError):
        mgr.prepare(lock)
    assert list(tmp_path.iterdir()) == []


def test_prepare_rejection_with_dry_run_still_raises(tmp_path: Path) -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    mgr = SourceManager(NeverCalledRunner(), cache_dir=tmp_path/"c", workspace_dir=tmp_path/"w")
    with pytest.raises(SourceLockUnresolvedError):
        mgr.prepare(lock, dry_run=True)


def test_status_flip_without_real_checksum_still_fails(tmp_path: Path) -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    if lock.status == "pinned":
        pytest.skip("source lock has been legitimately pinned")
    # Stronger than the original handoff: reject sentinel before cache inspection.
    mgr = SourceManager(NeverCalledRunner(), cache_dir=tmp_path/"c", workspace_dir=tmp_path/"w")
    with pytest.raises(SourceLockUnresolvedError, match="verified SHA-256"):
        mgr.prepare(replace(lock, status="pinned"), allow_network=False)
    assert list(tmp_path.iterdir()) == []


def test_notes_explain_how_to_resolve_when_unresolved() -> None:
    lock = SourceLock.load_from_path(LOCK_PATH)
    if lock.status == "unresolved":
        assert "unresolved" in lock.notes.lower()
        assert "checksum" in lock.notes.lower()
