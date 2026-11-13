"""Pinned kernel source retrieval, verification, and safe extraction.

Responsibilities
----------------
* Load and validate a :class:`SourceLock` against the pinned checksum.
* Reject untrusted URLs via :func:`huey.kernel_build.policy.check_url`.
* Cache/download the archive through the audited ``Runner`` (curl only,
  ``--proto '=https'``, redirects restricted to HTTPS).
* Verify SHA-256 for both cached and newly-downloaded archives; a
  mismatched download is deleted so the next run starts fresh.
* Extract ``.tar.{gz,xz,bz2}`` and ``.deb`` archives safely:
  ``tarfile.extractall(filter="data")`` plus a post-extraction
  verification pass that rejects escaping symlinks, hardlinks, ``..``
  path components, and special files.
* Write a ``.huey-source.marker`` file so that re-runs are idempotent.
* Offline by default: ``allow_network=False`` refuses to download unless
  the operator explicitly opts in.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import re
import shutil
import tarfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from huey.kernel_build.models import Severity, SourceType
from huey.kernel_build.policy import check_path_destination_safe, check_url
from huey.kernel_build.runner import (
    CommandSpec,
    RunnerError,
    RunnerProtocol,
    RunnerTimeout,
)

logger = logging.getLogger(__name__)

__all__ = [
    "DebExtractor",
    "SourceArchiveSymlinkError",
    "SourceArchiveTraversalError",
    "SourceCacheMissingError",
    "SourceChecksumMismatchError",
    "SourceDownloadError",
    "SourceLock",
    "SourceLockUnresolvedError",
    "SourceManager",
    "SourceManagerError",
    "SourceMaterial",
]

_MARKER_NAME = ".huey-source.marker"
_SUPPORTED_TAR_SUFFIXES = (
    ".tar",
    ".tar.gz",
    ".tgz",
    ".tar.bz2",
    ".tbz2",
    ".tar.xz",
    ".txz",
)
_SUPPORTED_DEB_SUFFIX = ".deb"

DebExtractor = Callable[[Path, Path], None]
"""Signature of a ``.deb`` extractor: ``(deb_path, target_dir) -> None``."""


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SourceManagerError(RuntimeError):
    """Base class for source-manager failures."""


class SourceLockUnresolvedError(SourceManagerError):
    """The lock is ``unresolved`` or its checksum field is not a valid SHA-256."""


class SourceChecksumMismatchError(SourceManagerError):
    """Computed SHA-256 does not match the pinned checksum."""


class SourceCacheMissingError(SourceManagerError):
    """Archive is not cached and network access was not authorized."""


class SourceDownloadError(SourceManagerError):
    """The download command failed (missing tool, nonzero exit, timeout)."""


class SourceArchiveTraversalError(SourceManagerError):
    """Archive contains a ``..`` component, absolute path, or otherwise unsafe entry."""


class SourceArchiveSymlinkError(SourceManagerError):
    """Extracted tree contains a symlink or hardlink that escapes the root."""


# ---------------------------------------------------------------------------
# SourceLock
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SourceLock:
    """Pinned identity of a kernel source archive."""

    schema_version: int
    status: str  # "unresolved" | "pinned"
    source_type: SourceType
    package_name: str
    version: str
    archive_filename: str
    origin_url: str
    checksum_sha256: str
    retrieved_date: str | None = None
    license: str = ""
    profile_revision: int | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.source_type, str):
            try:
                object.__setattr__(self, "source_type", SourceType(self.source_type))
            except ValueError as exc:
                raise ValueError(
                    f"SourceLock.source_type={self.source_type!r} is not valid"
                ) from exc
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("SourceLock.schema_version must be exactly 1")
        if not isinstance(self.source_type, SourceType):
            raise TypeError("SourceLock.source_type must be a SourceType")
        for name in ("package_name", "version", "archive_filename"):
            value = getattr(self, name)
            if not isinstance(value, str) or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9._+~-]*", value
            ) or ".." in value:
                raise ValueError(f"SourceLock.{name} must be a safe relative component")
        if not isinstance(self.origin_url, str) or not self.origin_url:
            raise ValueError("SourceLock.origin_url must be nonempty")
        if type(self.profile_revision) is not int and self.profile_revision is not None:
            raise TypeError("SourceLock.profile_revision must be int or None")
        if self.retrieved_date is not None and not isinstance(self.retrieved_date, str):
            raise TypeError("SourceLock.retrieved_date must be str or None")
        for name in ("license", "notes"):
            if not isinstance(getattr(self, name), str):
                raise TypeError(f"SourceLock.{name} must be str")
        if self.status not in {"unresolved", "pinned"}:
            raise ValueError(
                f"SourceLock.status must be 'unresolved' or 'pinned', got {self.status!r}"
            )
        if not _is_sha256(self.checksum_sha256):
            raise ValueError(
                "SourceLock.checksum_sha256 must be a 64-char lowercase hex SHA-256"
            )

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "source_type": self.source_type.value,
            "package_name": self.package_name,
            "version": self.version,
            "archive_filename": self.archive_filename,
            "origin_url": self.origin_url,
            "checksum_sha256": self.checksum_sha256,
            "retrieved_date": self.retrieved_date,
            "license": self.license,
            "profile_revision": self.profile_revision,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SourceLock:
        if not isinstance(data, dict):
            raise TypeError("SourceLock.from_dict expects a dict")
        required = (
            "schema_version",
            "status",
            "source_type",
            "package_name",
            "version",
            "archive_filename",
            "origin_url",
            "checksum_sha256",
        )
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"SourceLock missing required fields: {missing}")
        unexpected = set(data) - {
            "schema_version", "status", "source_type", "package_name",
            "version", "archive_filename", "origin_url", "checksum_sha256",
            "retrieved_date", "license", "profile_revision", "notes",
        }
        if unexpected:
            raise ValueError(f"SourceLock unknown fields: {sorted(unexpected)!r}")
        return cls(
            schema_version=data["schema_version"],
            status=data["status"],
            source_type=data["source_type"],
            package_name=data["package_name"],
            version=data["version"],
            archive_filename=data["archive_filename"],
            origin_url=data["origin_url"],
            checksum_sha256=data["checksum_sha256"],
            retrieved_date=data.get("retrieved_date"),
            license=data.get("license", ""),
            profile_revision=data.get("profile_revision"),
            notes=data.get("notes", ""),
        )

    @classmethod
    def load_from_path(cls, path: Path) -> SourceLock:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SourceManagerError(
                f"Failed to load source lock {path}: {exc}"
            ) from exc
        return cls.from_dict(data)


# ---------------------------------------------------------------------------
# SourceMaterial
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SourceMaterial:
    """Result of :meth:`SourceManager.prepare`."""

    workspace_dir: Path
    kernel_source_dir: Path | None  # None in dry_run before verification
    archive_path: Path | None  # None in dry_run before download
    archive_sha256: str
    lock: SourceLock
    extracted: bool
    dry_run: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        c in "0123456789abcdef" for c in value
    )


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _archive_kind(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(_SUPPORTED_DEB_SUFFIX):
        return "deb"
    for suffix in _SUPPORTED_TAR_SUFFIXES:
        if lower.endswith(suffix):
            return "tar"
    raise SourceManagerError(
        f"Unsupported archive type: {filename!r}. "
        f"Supported: {list(_SUPPORTED_TAR_SUFFIXES)} or {_SUPPORTED_DEB_SUFFIX}."
    )


# ---------------------------------------------------------------------------
# SourceManager
# ---------------------------------------------------------------------------


class SourceManager:
    """Pinned-source retrieval and safe extraction."""

    def __init__(
        self,
        runner: RunnerProtocol,
        *,
        cache_dir: Path,
        workspace_dir: Path,
        deb_extractor: DebExtractor | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._runner = runner
        self._cache_dir = Path(cache_dir)
        self._workspace_dir = Path(workspace_dir)
        self._deb_extractor: DebExtractor = deb_extractor or self._default_deb_extractor
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    # ---- public ---------------------------------------------------------

    def prepare(
        self,
        lock: SourceLock,
        *,
        allow_network: bool = False,
        dry_run: bool = False,
        force: bool = False,
    ) -> SourceMaterial:
        """Verify or fetch, then safely extract, the pinned kernel source.

        Raises
        ------
        SourceLockUnresolvedError
            ``lock.status`` is not ``pinned`` or the checksum is malformed.
        SourceManagerError
            The lock's ``origin_url`` fails trust checks, or the existing
            extraction state is inconsistent and ``force`` was not given.
        SourceCacheMissingError
            Archive is not cached and ``allow_network=False``.
        SourceDownloadError
            Download command failed.
        SourceChecksumMismatchError
            Computed SHA-256 differs from ``lock.checksum_sha256``.
        SourceArchiveTraversalError / SourceArchiveSymlinkError
            Archive contents are unsafe.
        """
        self._validate_lock(lock)
        self._validate_url(lock.origin_url)

        cache_path = self._cache_dir / lock.archive_filename
        extraction_root = self._workspace_dir / f"{lock.package_name}-{lock.version}"
        marker_path = extraction_root / _MARKER_NAME

        # Pure planning must not even inspect the cache, marker or filesystem.
        if dry_run:
            return SourceMaterial(
                workspace_dir=extraction_root, kernel_source_dir=None,
                archive_path=None, archive_sha256=lock.checksum_sha256,
                lock=lock, extracted=False, dry_run=True,
            )

        for destination in (self._cache_dir, self._workspace_dir, extraction_root):
            findings = check_path_destination_safe(destination)
            if any(f.severity in (Severity.ERROR, Severity.CRITICAL) for f in findings):
                raise SourceManagerError(f"Unsafe source destination: {destination}")
        if cache_path.is_symlink() or extraction_root.is_symlink() or marker_path.is_symlink():
            raise SourceManagerError("Refusing symlinked cache/archive/extraction marker")

        # Idempotent return if a matching marker exists and force is off.
        if not force and marker_path.exists():
            try:
                current_sha = marker_path.read_text(encoding="utf-8").strip()
            except OSError:
                current_sha = None
            if current_sha == lock.checksum_sha256:
                kernel_source_dir = self._find_kernel_source_dir(extraction_root)
                return SourceMaterial(
                    workspace_dir=extraction_root,
                    kernel_source_dir=kernel_source_dir,
                    archive_path=cache_path if cache_path.exists() else None,
                    archive_sha256=lock.checksum_sha256,
                    lock=lock,
                    extracted=False,
                    dry_run=dry_run,
                )

        # Ensure the archive is cached and its hash matches the pin.
        archive_available = cache_path.exists()
        if archive_available:
            if not cache_path.is_file():
                raise SourceManagerError("Cached archive is not a regular file")
            actual_sha = _sha256_file(cache_path)
            if actual_sha != lock.checksum_sha256:
                raise SourceChecksumMismatchError(
                    f"Cached archive {cache_path} has SHA-256 {actual_sha}, "
                    f"expected {lock.checksum_sha256}."
                )
        else:
            if not allow_network:
                raise SourceCacheMissingError(
                    f"Archive not cached at {cache_path} and allow_network=False. "
                    "Obtain the archive out-of-band, or pass allow_network=True."
                )
            self._download(lock.origin_url, cache_path)
            actual_sha = _sha256_file(cache_path)
            if actual_sha != lock.checksum_sha256:
                cache_path.unlink(missing_ok=True)
                raise SourceChecksumMismatchError(
                    f"Downloaded archive SHA-256 {actual_sha} != "
                    f"expected {lock.checksum_sha256}; cache removed."
                )

        # Handle existing extraction dir without a matching marker.
        if extraction_root.exists():
            if not force:
                raise SourceManagerError(
                    f"Extraction directory {extraction_root} exists without a "
                    "matching marker. Use force=True to re-prepare, or remove "
                    "it manually."
                )
            shutil.rmtree(extraction_root)

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._workspace_dir.mkdir(parents=True, exist_ok=True)

        tmp_extraction = (
            self._workspace_dir / f".{extraction_root.name}.tmp.{uuid.uuid4().hex}"
        )
        tmp_extraction.mkdir()
        try:
            self._extract_archive(cache_path, tmp_extraction)
            self.verify_extracted_tree(tmp_extraction)
            (tmp_extraction / _MARKER_NAME).write_text(
                lock.checksum_sha256, encoding="utf-8"
            )
            tmp_extraction.rename(extraction_root)
        except BaseException:
            shutil.rmtree(tmp_extraction, ignore_errors=True)
            raise

        kernel_source_dir = self._find_kernel_source_dir(extraction_root)
        logger.info(
            "source.prepared kernel_source_dir=%s archive=%s sha256=%s",
            kernel_source_dir,
            cache_path,
            lock.checksum_sha256,
        )
        return SourceMaterial(
            workspace_dir=extraction_root,
            kernel_source_dir=kernel_source_dir,
            archive_path=cache_path,
            archive_sha256=lock.checksum_sha256,
            lock=lock,
            extracted=True,
            dry_run=False,
        )

    def verify_extracted_tree(self, root: Path) -> None:
        """Post-extraction defense-in-depth check (public for tests).

        ``tarfile.extractall(filter="data")`` already refuses traversal,
        escaping symlinks, absolute paths, and special files. This pass runs
        independently so the framework is not solely dependent on the
        standard library's filter implementation.
        """
        root_resolved = root.resolve()
        for entry in root.rglob("*"):
            rel = entry.relative_to(root)
            if rel.name == _MARKER_NAME:
                continue
            if ".." in rel.parts:
                raise SourceArchiveTraversalError(
                    f"Extracted path contains '..': {entry}"
                )
            if entry.is_symlink():
                try:
                    target = entry.resolve(strict=False)
                except (OSError, RuntimeError) as exc:
                    raise SourceArchiveSymlinkError(
                        f"Unresolvable symlink in extraction: {entry}: {exc}"
                    ) from exc
                try:
                    target.relative_to(root_resolved)
                except ValueError:
                    raise SourceArchiveSymlinkError(
                        f"Symlink escapes extraction root: {entry} -> {target}"
                    )
            elif not (entry.is_file() or entry.is_dir()):
                raise SourceManagerError(
                    f"Special file (device, FIFO, or socket) in extraction: {entry}"
                )

    # ---- internal -------------------------------------------------------

    def _validate_lock(self, lock: SourceLock) -> None:
        if lock.status != "pinned":
            raise SourceLockUnresolvedError(
                f"Source lock is {lock.status!r}; resolve and pin the source "
                "in source.lock.json before proceeding."
            )
        if not _is_sha256(lock.checksum_sha256) or lock.checksum_sha256 == "0" * 64:
            raise SourceLockUnresolvedError(
                "Source lock checksum is not a verified SHA-256 pin."
            )

    def _validate_url(self, url: str) -> None:
        findings = check_url(url)
        blocking = [
            f for f in findings if f.severity in (Severity.ERROR, Severity.CRITICAL)
        ]
        if blocking:
            raise SourceManagerError(
                f"Source URL rejected: {blocking[0].message}"
            )

    def _download(self, url: str, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        spec = CommandSpec(
            argv=(
                "curl",
                "-fsSL",
                "--proto",
                "=https",
                "--proto-redir",
                "=https",
                "--max-time",
                "600",
                "-o",
                str(dest),
                url,
            ),
            cwd=dest.parent,
            description=f"Download {url}",
            timeout_seconds=650.0,
        )
        try:
            result = self._runner.run(spec)
        except RunnerTimeout as exc:
            # curl may already have written partial bytes before the timeout.
            # This path was absent before the download and belongs to us.
            dest.unlink(missing_ok=True)
            raise SourceDownloadError(
                f"curl timed out downloading {url}: {exc}"
            ) from exc
        except RunnerError as exc:
            dest.unlink(missing_ok=True)
            raise SourceDownloadError(
                f"curl failed to launch for {url}: {exc}"
            ) from exc
        if not result.succeeded:
            dest.unlink(missing_ok=True)
            raise SourceDownloadError(
                f"curl returned {result.command.returncode} downloading {url}"
            )

    def _extract_archive(self, archive_path: Path, target: Path) -> None:
        kind = _archive_kind(archive_path.name)
        if kind == "deb":
            self._extract_deb(archive_path, target)
        else:
            self._extract_tar(archive_path, target)

    def _extract_tar(self, archive_path: Path, target: Path) -> None:
        try:
            with tarfile.open(archive_path, "r:*") as tf:
                for member in tf.getmembers():
                    member_path = Path(member.name)
                    if (member_path.is_absolute() or ".." in member_path.parts
                            or member.islnk() or not (
                                member.isfile() or member.isdir() or member.issym()
                            )):
                        raise SourceArchiveTraversalError(
                            f"Unsafe archive member: {member.name!r}"
                        )
                tf.extractall(target, filter="data")
        except tarfile.TarError as exc:
            raise SourceArchiveTraversalError(
                f"Refusing unsafe tar {archive_path.name}: {exc}"
            ) from exc
        except (EOFError, OSError) as exc:
            raise SourceManagerError(
                f"Failed to extract {archive_path.name}: {exc}"
            ) from exc

    def _extract_deb(self, deb_path: Path, target: Path) -> None:
        staging = target / ".deb-extraction"
        staging.mkdir(parents=True, exist_ok=True)
        try:
            self._deb_extractor(deb_path, staging)
            self.verify_extracted_tree(staging)
            candidates = sorted(
                p
                for p in staging.rglob("linux-source-*.tar.*")
                if p.is_file() and not p.is_symlink()
            )
            if not candidates:
                raise SourceManagerError(
                    f"No linux-source-*.tar.* found inside {deb_path.name}; "
                    "cannot determine the kernel source archive."
                )
            self._extract_tar(candidates[0], target)
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def _default_deb_extractor(self, deb_path: Path, target_dir: Path) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        spec = CommandSpec(
            argv=("dpkg-deb", "-x", str(deb_path), str(target_dir)),
            cwd=target_dir.parent,
            description=f"Extract {deb_path.name}",
            timeout_seconds=300.0,
        )
        try:
            result = self._runner.run(spec)
        except (RunnerError, RunnerTimeout) as exc:
            raise SourceManagerError(
                f"dpkg-deb failed to launch for {deb_path.name}: {exc}"
            ) from exc
        if not result.succeeded:
            raise SourceManagerError(
                f"dpkg-deb returned {result.command.returncode} for {deb_path.name}"
            )

    def _find_kernel_source_dir(self, root: Path) -> Path:
        entries = [e for e in root.iterdir() if e.name != _MARKER_NAME]
        if len(entries) == 1 and entries[0].is_dir():
            candidate = entries[0]
        else:
            candidate = root
        if not (candidate / "Makefile").exists():
            raise SourceManagerError(
                f"Extracted tree does not contain a kernel Makefile at {candidate}"
            )
        return candidate


# Keep `io` imported for tests that construct in-memory tars; do not remove.
_ = io
