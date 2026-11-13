"""Canonical offline source-manager regression suite (Steps 8 and 37)."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from huey.kernel_build.models import CommandResult, SourceType
from huey.kernel_build.runner import (
    CommandSpec,
    RunnerError,
    RunnerResult,
    RunnerTimeout,
)
from huey.kernel_build.source_manager import (
    SourceArchiveSymlinkError,
    SourceArchiveTraversalError,
    SourceCacheMissingError,
    SourceChecksumMismatchError,
    SourceDownloadError,
    SourceLock,
    SourceLockUnresolvedError,
    SourceManager,
    SourceManagerError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_valid_tar(path: Path, *, compression: str = "gz", top: str = "linux-7.2.15") -> str:
    with tarfile.open(path, f"w:{compression}") as tf:
        d = tarfile.TarInfo(name=f"{top}/")
        d.type = tarfile.DIRTYPE
        d.mode = 0o755
        tf.addfile(d)
        content = b"# fake kernel Makefile\n"
        f = tarfile.TarInfo(name=f"{top}/Makefile")
        f.size = len(content)
        f.mode = 0o644
        tf.addfile(f, io.BytesIO(content))
    return _sha256_bytes(path.read_bytes())


def _write_traversal_tar(path: Path) -> str:
    with tarfile.open(path, "w:gz") as tf:
        content = b"pwned"
        f = tarfile.TarInfo(name="../escape.txt")
        f.size = len(content)
        tf.addfile(f, io.BytesIO(content))
    return _sha256_bytes(path.read_bytes())


def _write_symlink_escape_tar(path: Path) -> str:
    with tarfile.open(path, "w:gz") as tf:
        d = tarfile.TarInfo(name="src/")
        d.type = tarfile.DIRTYPE
        d.mode = 0o755
        tf.addfile(d)
        link = tarfile.TarInfo(name="src/evil")
        link.type = tarfile.SYMTYPE
        link.linkname = "../../../etc/passwd"
        tf.addfile(link)
    return _sha256_bytes(path.read_bytes())


class FakeRunner:
    def __init__(self) -> None:
        self._handlers: dict[tuple[str, ...], callable] = {}
        self._calls: list[CommandSpec] = []

    def on(self, prefix, handler):
        self._handlers[prefix] = handler
        return self

    def run(self, spec: CommandSpec, *, dry_run: bool = False) -> RunnerResult:
        self._calls.append(spec)
        for prefix in sorted(self._handlers, key=len, reverse=True):
            if spec.argv[: len(prefix)] == prefix:
                return self._handlers[prefix](spec)
        raise RunnerError(f"FakeRunner: no handler for argv={spec.argv!r}")

    @property
    def calls(self):
        return tuple(self._calls)


def _result(argv, *, stdout=b"", returncode=0, cwd="/") -> RunnerResult:
    return RunnerResult(
        command=CommandResult(argv=argv, cwd=cwd, returncode=returncode, elapsed_seconds=0.0),
        executed=True,
        dry_run=False,
        stdout=stdout,
        stderr=b"",
        output_truncated=False,
    )


def _lock(path: Path, *, url="https://deb.debian.org/debian/pool/main/l/linux/linux.tar.xz",
          filename: str | None = None, status: str = "pinned") -> SourceLock:
    sha = _sha256_bytes(path.read_bytes()) if path.exists() else "0" * 64
    return SourceLock(
        schema_version=1,
        status=status,
        source_type=SourceType.UPSTREAM,
        package_name="linux",
        version="7.2.15",
        archive_filename=filename or path.name,
        origin_url=url,
        checksum_sha256=sha,
    )


def _download_handler(src: Path):
    """Handler that copies ``src`` to ``-o`` destination (simulates curl)."""
    def handler(spec: CommandSpec) -> RunnerResult:
        idx = spec.argv.index("-o")
        dest = Path(spec.argv[idx + 1])
        dest.write_bytes(src.read_bytes())
        return _result(spec.argv)
    return handler


# ---------------------------------------------------------------------------
# Lock validation
# ---------------------------------------------------------------------------


def test_unresolved_lock_raises(tmp_path: Path) -> None:
    mgr = SourceManager(FakeRunner(), cache_dir=tmp_path/"c", workspace_dir=tmp_path/"w")
    lock = SourceLock(
        schema_version=1, status="unresolved", source_type=SourceType.UPSTREAM,
        package_name="linux", version="7.2.15", archive_filename="x.tar.xz",
        origin_url="https://deb.debian.org/x.tar.xz", checksum_sha256="0"*64,
    )
    with pytest.raises(SourceLockUnresolvedError):
        mgr.prepare(lock)


def test_lock_with_bad_checksum_rejected_at_construction(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        SourceLock(
            schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
            package_name="linux", version="1", archive_filename="x.tar.gz",
            origin_url="https://deb.debian.org/x", checksum_sha256="not-a-hash",
        )


def test_lock_from_dict_and_to_dict_round_trip(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    _write_valid_tar(tar)
    lock = _lock(tar)
    assert SourceLock.from_dict(lock.to_dict()) == lock


def test_lock_load_from_path(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    _write_valid_tar(tar)
    lock = _lock(tar)
    path = tmp_path / "source.lock.json"
    import json
    path.write_text(json.dumps(lock.to_dict()), encoding="utf-8")
    assert SourceLock.load_from_path(path) == lock


# ---------------------------------------------------------------------------
# URL trust
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "http://deb.debian.org/x.tar.xz",
        "https://example.com/x.tar.xz",
        "file:///tmp/x.tar.xz",
    ],
)
def test_untrusted_url_raises(url: str, tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    _write_valid_tar(tar)
    lock = _lock(tar, url=url)
    mgr = SourceManager(FakeRunner(), cache_dir=tmp_path/"c", workspace_dir=tmp_path/"w")
    with pytest.raises(SourceManagerError, match="URL rejected"):
        mgr.prepare(lock, allow_network=False)


# ---------------------------------------------------------------------------
# Cache-missing / SHA mismatch
# ---------------------------------------------------------------------------


def test_missing_cache_offline_raises(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    sha = _write_valid_tar(tar)
    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
        package_name="linux", version="7.2.15", archive_filename="linux.tar.gz",
        origin_url="https://deb.debian.org/debian/x", checksum_sha256=sha,
    )
    mgr = SourceManager(FakeRunner(), cache_dir=tmp_path/"cache", workspace_dir=tmp_path/"ws")
    with pytest.raises(SourceCacheMissingError):
        mgr.prepare(lock, allow_network=False)


def test_cached_archive_sha_mismatch_raises(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "linux.tar.gz").write_bytes(b"garbage content")
    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
        package_name="linux", version="7.2.15", archive_filename="linux.tar.gz",
        origin_url="https://deb.debian.org/debian/x",
        checksum_sha256="a" * 64,  # does not match
    )
    mgr = SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=tmp_path/"ws")
    with pytest.raises(SourceChecksumMismatchError):
        mgr.prepare(lock)


def test_download_sha_mismatch_removes_cache(tmp_path: Path) -> None:
    src = tmp_path / "src.tar.gz"
    _write_valid_tar(src)
    cache = tmp_path / "cache"
    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
        package_name="linux", version="7.2.15", archive_filename="linux.tar.gz",
        origin_url="https://deb.debian.org/debian/x",
        checksum_sha256="b" * 64,  # will not match downloaded content
    )
    runner = FakeRunner().on(("curl",), _download_handler(src))
    mgr = SourceManager(runner, cache_dir=cache, workspace_dir=tmp_path/"ws")
    with pytest.raises(SourceChecksumMismatchError):
        mgr.prepare(lock, allow_network=True)
    # Cache must not retain the bad download
    assert not (cache / "linux.tar.gz").exists()


def test_download_command_failure_raises(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
        package_name="linux", version="7.2.15", archive_filename="linux.tar.gz",
        origin_url="https://deb.debian.org/debian/x",
        checksum_sha256="c" * 64,
    )
    runner = FakeRunner().on(("curl",), lambda s: _result(s.argv, returncode=22))
    mgr = SourceManager(runner, cache_dir=cache, workspace_dir=tmp_path/"ws")
    with pytest.raises(SourceDownloadError):
        mgr.prepare(lock, allow_network=True)


# ---------------------------------------------------------------------------
# Happy path + idempotency
# ---------------------------------------------------------------------------


def test_happy_path_cached_tar_gz(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    sha = _write_valid_tar(tar)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "linux.tar.gz").write_bytes(tar.read_bytes())
    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
        package_name="linux", version="7.2.15", archive_filename="linux.tar.gz",
        origin_url="https://deb.debian.org/debian/x", checksum_sha256=sha,
    )
    mgr = SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=tmp_path/"ws")
    material = mgr.prepare(lock, allow_network=False)

    assert material.extracted is True
    assert material.dry_run is False
    assert material.kernel_source_dir is not None
    assert (material.kernel_source_dir / "Makefile").is_file()
    assert material.kernel_source_dir.name == "linux-7.2.15"
    assert material.archive_path == cache / "linux.tar.gz"
    assert material.archive_sha256 == sha


def test_idempotency_second_run(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    sha = _write_valid_tar(tar)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "linux.tar.gz").write_bytes(tar.read_bytes())
    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
        package_name="linux", version="7.2.15", archive_filename="linux.tar.gz",
        origin_url="https://deb.debian.org/debian/x", checksum_sha256=sha,
    )
    mgr = SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=tmp_path/"ws")
    first = mgr.prepare(lock)
    second = mgr.prepare(lock)
    assert first.extracted is True
    assert second.extracted is False  # marker found; no re-extraction
    assert first.kernel_source_dir == second.kernel_source_dir


def test_existing_extraction_without_marker_raises(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    sha = _write_valid_tar(tar)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "linux.tar.gz").write_bytes(tar.read_bytes())
    ws = tmp_path / "ws"
    stray = ws / "linux-7.2.15"
    stray.mkdir(parents=True)
    (stray / "Makefile").write_text("# stray\n", encoding="utf-8")
    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
        package_name="linux", version="7.2.15", archive_filename="linux.tar.gz",
        origin_url="https://deb.debian.org/debian/x", checksum_sha256=sha,
    )
    mgr = SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=ws)
    with pytest.raises(SourceManagerError, match="matching marker"):
        mgr.prepare(lock)


def test_force_reprepares_existing(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    sha = _write_valid_tar(tar)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "linux.tar.gz").write_bytes(tar.read_bytes())
    ws = tmp_path / "ws"
    stray = ws / "linux-7.2.15"
    stray.mkdir(parents=True)
    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
        package_name="linux", version="7.2.15", archive_filename="linux.tar.gz",
        origin_url="https://deb.debian.org/debian/x", checksum_sha256=sha,
    )
    mgr = SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=ws)
    material = mgr.prepare(lock, force=True)
    assert material.extracted is True


def test_dry_run_does_no_io(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    sha = _write_valid_tar(tar)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "linux.tar.gz").write_bytes(tar.read_bytes())
    ws = tmp_path / "ws"
    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
        package_name="linux", version="7.2.15", archive_filename="linux.tar.gz",
        origin_url="https://deb.debian.org/debian/x", checksum_sha256=sha,
    )
    mgr = SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=ws)
    material = mgr.prepare(lock, dry_run=True)
    assert material.dry_run is True
    assert material.extracted is False
    assert not ws.exists()  # no extraction dirs created


# ---------------------------------------------------------------------------
# Unsafe archives
# ---------------------------------------------------------------------------


def test_traversal_tar_rejected(tmp_path: Path) -> None:
    tar = tmp_path / "evil.tar.gz"
    sha = _write_traversal_tar(tar)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "evil.tar.gz").write_bytes(tar.read_bytes())
    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
        package_name="evil", version="1", archive_filename="evil.tar.gz",
        origin_url="https://deb.debian.org/debian/evil.tar.gz", checksum_sha256=sha,
    )
    mgr = SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=tmp_path/"ws")
    with pytest.raises(SourceArchiveTraversalError):
        mgr.prepare(lock)
    # No partial extraction left behind
    assert not (tmp_path/"ws"/"evil-1").exists()


def test_symlink_escape_tar_rejected(tmp_path: Path) -> None:
    tar = tmp_path / "evil.tar.gz"
    sha = _write_symlink_escape_tar(tar)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "evil.tar.gz").write_bytes(tar.read_bytes())
    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
        package_name="evil", version="1", archive_filename="evil.tar.gz",
        origin_url="https://deb.debian.org/debian/evil.tar.gz", checksum_sha256=sha,
    )
    mgr = SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=tmp_path/"ws")
    with pytest.raises((SourceArchiveTraversalError, SourceArchiveSymlinkError)):
        mgr.prepare(lock)


def test_verify_extracted_tree_catches_manual_symlink_escape(tmp_path: Path) -> None:
    """Defense-in-depth: post-extraction check rejects escaping symlink."""
    root = tmp_path / "extracted"
    root.mkdir()
    (root / "sub").mkdir()
    (root / "sub" / "evil").symlink_to("/etc/passwd")
    mgr = SourceManager(FakeRunner(), cache_dir=tmp_path/"c", workspace_dir=tmp_path/"w")
    with pytest.raises(SourceArchiveSymlinkError):
        mgr.verify_extracted_tree(root)


def test_verify_extracted_tree_accepts_in_root_symlink(tmp_path: Path) -> None:
    root = tmp_path / "extracted"
    root.mkdir()
    (root / "real.txt").write_text("hi", encoding="utf-8")
    (root / "link").symlink_to(root / "real.txt")
    mgr = SourceManager(FakeRunner(), cache_dir=tmp_path/"c", workspace_dir=tmp_path/"w")
    mgr.verify_extracted_tree(root)  # no exception


def test_unsupported_archive_suffix(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "linux.tar.zst").write_bytes(b"not real")
    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
        package_name="linux", version="7.2.15", archive_filename="linux.tar.zst",
        origin_url="https://deb.debian.org/debian/linux.tar.zst",
        checksum_sha256=_sha256_bytes(b"not real"),
    )
    mgr = SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=tmp_path/"ws")
    with pytest.raises(SourceManagerError, match="Unsupported archive"):
        mgr.prepare(lock)


# ---------------------------------------------------------------------------
# .deb via injectable extractor
# ---------------------------------------------------------------------------


def test_deb_extracts_inner_tarball(tmp_path: Path) -> None:
    # Valid inner tar.gz that the fake deb_extractor will place inside the deb
    inner = tmp_path / "inner.tar.gz"
    _write_valid_tar(inner, top="linux-source-7.2")
    deb_bytes = b"fake deb wrapper bytes"
    deb = tmp_path / "linux-source-7.2_7.2.15-1_all.deb"
    deb.write_bytes(deb_bytes)
    sha = _sha256_bytes(deb_bytes)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / deb.name).write_bytes(deb_bytes)

    def fake_extractor(deb_path: Path, target_dir: Path) -> None:
        dst = target_dir / "usr" / "src"
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "linux-source-7.2.tar.gz").write_bytes(inner.read_bytes())

    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.DEBIAN_LINUX_SOURCE,
        package_name="linux-source-7.2", version="7.2.15-1",
        archive_filename=deb.name,
        origin_url=f"https://deb.debian.org/debian/pool/main/l/linux/{deb.name}",
        checksum_sha256=sha,
    )
    mgr = SourceManager(
        FakeRunner(), cache_dir=cache, workspace_dir=tmp_path/"ws",
        deb_extractor=fake_extractor,
    )
    material = mgr.prepare(lock)
    assert material.extracted is True
    assert material.kernel_source_dir is not None
    assert (material.kernel_source_dir / "Makefile").is_file()
    assert material.kernel_source_dir.name == "linux-source-7.2"


def test_deb_without_inner_tarball_raises(tmp_path: Path) -> None:
    deb_bytes = b"fake deb without tarball"
    deb = tmp_path / "linux-source-7.2_7.2.15-1_all.deb"
    deb.write_bytes(deb_bytes)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / deb.name).write_bytes(deb_bytes)
    sha = _sha256_bytes(deb_bytes)

    def empty_extractor(deb_path: Path, target_dir: Path) -> None:
        (target_dir / "empty").mkdir(parents=True, exist_ok=True)

    lock = SourceLock(
        schema_version=1, status="pinned", source_type=SourceType.DEBIAN_LINUX_SOURCE,
        package_name="linux-source-7.2", version="7.2.15-1",
        archive_filename=deb.name,
        origin_url=f"https://deb.debian.org/debian/pool/main/l/linux/{deb.name}",
        checksum_sha256=sha,
    )
    mgr = SourceManager(
        FakeRunner(), cache_dir=cache, workspace_dir=tmp_path/"ws",
        deb_extractor=empty_extractor,
    )
    with pytest.raises(SourceManagerError, match="linux-source"):
        mgr.prepare(lock)

# ---------------------------------------------------------------------------
# Additional adversarial checks: no lock-controlled path escapes or dry-run I/O
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field,bad", [
    ("archive_filename", "../../boot/evil.tar.gz"),
    ("archive_filename", "/etc/passwd"),
    ("archive_filename", "../bad.tar.gz"),
    ("package_name", "../../etc"),
    ("version", "../../boot"),
    ("version", ""),
])
def test_source_lock_rejects_unsafe_path_components(field: str, bad: str, tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    _write_valid_tar(tar)
    data = _lock(tar).to_dict()
    data[field] = bad
    with pytest.raises(ValueError, match="safe relative component"):
        SourceLock.from_dict(data)


def test_status_flip_with_all_zero_checksum_blocks_even_dry_run(tmp_path: Path) -> None:
    data = {
        "schema_version": 1, "status": "pinned", "source_type": "upstream",
        "package_name": "linux", "version": "1", "archive_filename": "linux.tar.gz",
        "origin_url": "https://deb.debian.org/x.tar.gz", "checksum_sha256": "0" * 64,
    }
    mgr = SourceManager(FakeRunner(), cache_dir=tmp_path/"cache", workspace_dir=tmp_path/"ws")
    with pytest.raises(SourceLockUnresolvedError):
        mgr.prepare(SourceLock.from_dict(data), dry_run=True)
    assert list(tmp_path.iterdir()) == []


def test_dry_run_never_checks_file_presence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tar = tmp_path / "linux.tar.gz"
    sha = _write_valid_tar(tar)
    lock = SourceLock.from_dict({
        "schema_version": 1, "status": "pinned", "source_type": "upstream",
        "package_name": "linux", "version": "1", "archive_filename": "linux.tar.gz",
        "origin_url": "https://deb.debian.org/x.tar.gz", "checksum_sha256": sha,
    })
    runner = FakeRunner()
    mgr = SourceManager(runner, cache_dir=tmp_path/"cache", workspace_dir=tmp_path/"ws")
    def fail_exists(_self: Path) -> bool:
        raise AssertionError("dry-run must not stat the filesystem")
    monkeypatch.setattr(Path, "exists", fail_exists)
    planned = mgr.prepare(lock, dry_run=True)
    assert planned.dry_run and not planned.extracted
    assert planned.archive_path is None and planned.kernel_source_dir is None
    assert runner.calls == ()


def test_cache_symlink_refused(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    sha = _write_valid_tar(tar)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "linux.tar.gz").symlink_to(tar)
    lock = _lock(tar)
    mgr = SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=tmp_path/"ws")
    with pytest.raises(SourceManagerError, match="symlinked"):
        mgr.prepare(lock)
    assert tar.exists() and tar.is_file()


def test_protected_workspace_refused_before_writes(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    _write_valid_tar(tar)
    lock = _lock(tar)
    # /boot is a host-protected destination, regardless of cache status.
    mgr = SourceManager(FakeRunner(), cache_dir=tmp_path / "cache", workspace_dir=Path("/boot/huey-test"))
    with pytest.raises(SourceManagerError, match="Unsafe source destination"):
        mgr.prepare(lock)


def test_source_lock_strict_schema_rejects_unrecognized_fields(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    _write_valid_tar(tar)
    data = _lock(tar).to_dict()
    data["unsafe_auto_install"] = True
    with pytest.raises(ValueError, match="unknown fields"):
        SourceLock.from_dict(data)


def test_source_lock_rejects_numeric_coercion(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    _write_valid_tar(tar)
    data = _lock(tar).to_dict()
    data["schema_version"] = "1"
    with pytest.raises(ValueError, match="schema_version"):
        SourceLock.from_dict(data)


# ---------------------------------------------------------------------------
# Step 37: further canonical contract coverage
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("checksum", ["a" * 63, "A" * 64, "a" * 63 + "B", "g" * 64])
def test_source_lock_rejects_malformed_sha256(checksum: str) -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        SourceLock(
            schema_version=1, status="pinned", source_type=SourceType.UPSTREAM,
            package_name="linux", version="7.2.15", archive_filename="linux.tar.gz",
            origin_url="https://deb.debian.org/linux.tar.gz", checksum_sha256=checksum,
        )


def test_source_lock_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="status"):
        SourceLock(
            schema_version=1, status="maybe", source_type=SourceType.UPSTREAM,
            package_name="linux", version="7.2.15", archive_filename="linux.tar.gz",
            origin_url="https://deb.debian.org/linux.tar.gz", checksum_sha256="a" * 64,
        )


def test_source_lock_missing_required_from_dict() -> None:
    with pytest.raises(ValueError, match="missing required fields"):
        SourceLock.from_dict({"status": "pinned", "schema_version": 1})


def test_source_lock_rejects_non_dict_from_dict() -> None:
    with pytest.raises(TypeError, match="dict"):
        SourceLock.from_dict(["not", "a", "dict"])  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_content", ["invalid JSON", "[1, 2, 3]"])
def test_source_lock_load_from_path_bad_json_or_type(tmp_path: Path, bad_content: str) -> None:
    p = tmp_path / "source.lock.json"
    p.write_text(bad_content, encoding="utf-8")
    with pytest.raises((SourceManagerError, TypeError)):
        SourceLock.load_from_path(p)


def test_source_lock_load_from_path_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SourceManagerError, match="Failed to load"):
        SourceLock.load_from_path(tmp_path / "missing.json")


@pytest.mark.parametrize("url", [
    "ftp://deb.debian.org/linux.tar.gz",
    "https:///missing-host.tar.gz",
])
def test_source_url_extra_schemes_refused_before_subprocess(tmp_path: Path, url: str) -> None:
    tar = tmp_path / "linux.tar.gz"
    _write_valid_tar(tar)
    runner = FakeRunner()
    mgr = SourceManager(runner, cache_dir=tmp_path / "cache", workspace_dir=tmp_path / "ws")
    with pytest.raises(SourceManagerError, match="URL rejected"):
        mgr.prepare(_lock(tar, url=url), allow_network=False)
    assert runner.calls == ()
    assert not (tmp_path / "cache").exists()
    assert not (tmp_path / "ws").exists()


def test_cached_checksum_failure_preserves_operator_cache(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    tar = cache / "linux.tar.gz"
    tar.write_bytes(b"cache supplied by operator")
    data = _lock(tar).to_dict()
    data["checksum_sha256"] = "a" * 64
    with pytest.raises(SourceChecksumMismatchError):
        SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=tmp_path / "ws").prepare(
            SourceLock.from_dict(data)
        )
    assert tar.read_bytes() == b"cache supplied by operator"


def test_download_timeout_cleans_partial_cache(tmp_path: Path) -> None:
    tar = tmp_path / "valid.tar.gz"
    sha = _write_valid_tar(tar)
    data = _lock(tar, filename="linux.tar.gz").to_dict()
    data["checksum_sha256"] = sha

    def interrupt(spec: CommandSpec) -> RunnerResult:
        dest = Path(spec.argv[spec.argv.index("-o") + 1])
        dest.write_bytes(b"partial data")
        raise RunnerTimeout("curl exceeded deadline")

    runner = FakeRunner().on(("curl",), interrupt)
    cache = tmp_path / "cache"
    mgr = SourceManager(runner, cache_dir=cache, workspace_dir=tmp_path / "ws")
    with pytest.raises(SourceDownloadError, match="timed out"):
        mgr.prepare(SourceLock.from_dict(data), allow_network=True)
    assert not (cache / "linux.tar.gz").exists()
    assert len(runner.calls) == 1


def test_download_runner_failure_cleans_partial_cache(tmp_path: Path) -> None:
    tar = tmp_path / "valid.tar.gz"
    _write_valid_tar(tar)
    data = _lock(tar, filename="linux.tar.gz").to_dict()

    def interrupt(spec: CommandSpec) -> RunnerResult:
        Path(spec.argv[spec.argv.index("-o") + 1]).write_bytes(b"partial data")
        raise RunnerError("curl failed to execute")

    runner = FakeRunner().on(("curl",), interrupt)
    cache = tmp_path / "cache"
    with pytest.raises(SourceDownloadError, match="failed to launch"):
        SourceManager(runner, cache_dir=cache, workspace_dir=tmp_path / "ws").prepare(
            SourceLock.from_dict(data), allow_network=True,
        )
    assert not (cache / "linux.tar.gz").exists()


@pytest.mark.parametrize("ext,compression", [("xz", "xz"), ("bz2", "bz2")])
def test_multiple_tar_compressions(tmp_path: Path, ext: str, compression: str) -> None:
    tar = tmp_path / f"linux.tar.{ext}"
    _write_valid_tar(tar, compression=compression)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / tar.name).write_bytes(tar.read_bytes())
    output = SourceManager(
        FakeRunner(), cache_dir=cache, workspace_dir=tmp_path / "ws",
    ).prepare(_lock(tar), allow_network=False)
    assert output.extracted and output.kernel_source_dir is not None
    assert (output.kernel_source_dir / "Makefile").is_file()


def test_stale_marker_refuses_to_erase_existing_tree_without_force(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    _write_valid_tar(tar)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / tar.name).write_bytes(tar.read_bytes())
    mgr = SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=tmp_path / "ws")
    lock = _lock(tar)
    first = mgr.prepare(lock)
    marker = first.workspace_dir / ".huey-source.marker"
    marker.write_text("0" * 64, encoding="utf-8")
    # Do not silently delete an operator-modified directory: require force.
    with pytest.raises(SourceManagerError, match="matching marker"):
        mgr.prepare(lock)
    assert (first.kernel_source_dir / "Makefile").is_file()
    repaired = mgr.prepare(lock, force=True)
    assert repaired.extracted
    assert marker.read_text(encoding="utf-8") == lock.checksum_sha256


def test_dry_run_offline_missing_cache_does_not_read_filesystem(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tar = tmp_path / "linux.tar.gz"
    _write_valid_tar(tar)
    lock = _lock(tar)
    runner = FakeRunner()
    mgr = SourceManager(runner, cache_dir=tmp_path / "cache", workspace_dir=tmp_path / "ws")
    # Step 8's stronger contract: dry_run is pure planning, no stat(), even
    # when offline cache is missing. A later real run will reject the cache.
    def forbid_exists(_self: Path) -> bool:
        raise AssertionError("dry run must not inspect cache")
    monkeypatch.setattr(Path, "exists", forbid_exists)
    result = mgr.prepare(lock, dry_run=True, allow_network=False)
    assert result.dry_run and not result.extracted
    assert result.archive_path is None and result.kernel_source_dir is None
    assert runner.calls == ()


def test_absolute_tar_member_rejected(tmp_path: Path) -> None:
    tar = tmp_path / "evil.tar.gz"
    with tarfile.open(tar, "w:gz") as tf:
        data = b"unsafe"
        member = tarfile.TarInfo("/etc/evil")
        member.size = len(data)
        tf.addfile(member, io.BytesIO(data))
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / tar.name).write_bytes(tar.read_bytes())
    with pytest.raises(SourceArchiveTraversalError):
        SourceManager(FakeRunner(), cache_dir=cache, workspace_dir=tmp_path / "ws").prepare(
            _lock(tar), allow_network=False,
        )
    assert not (tmp_path / "ws" / "linux-7.2.15").exists()


def test_deb_extractor_is_never_called_for_tarball(tmp_path: Path) -> None:
    tar = tmp_path / "linux.tar.gz"
    _write_valid_tar(tar)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / tar.name).write_bytes(tar.read_bytes())
    called = []

    def forbidden_extractor(_archive: Path, _target: Path) -> None:
        called.append(_archive)
        raise AssertionError("deb extractor invoked on tarball")

    mgr = SourceManager(
        FakeRunner(), cache_dir=cache, workspace_dir=tmp_path / "ws",
        deb_extractor=forbidden_extractor,
    )
    assert mgr.prepare(_lock(tar), allow_network=False).extracted
    assert called == []


def test_unresolved_lock_has_zero_side_effects(tmp_path: Path) -> None:
    lock = SourceLock(
        schema_version=1, status="unresolved", source_type=SourceType.UPSTREAM,
        package_name="linux", version="7.2.15", archive_filename="linux.tar.gz",
        origin_url="https://deb.debian.org/linux.tar.gz", checksum_sha256="0" * 64,
    )
    runner = FakeRunner()
    mgr = SourceManager(runner, cache_dir=tmp_path / "cache", workspace_dir=tmp_path / "ws")
    with pytest.raises(SourceLockUnresolvedError):
        mgr.prepare(lock)
    assert runner.calls == ()
    assert list(tmp_path.iterdir()) == []
