"""Release assembly for the HueyOS kernel build framework.

Collects only validated outputs into a versioned release directory.

Refusals (fail-closed):
* ``ctx.verification.boot_ready`` is False or has any ERROR/CRITICAL finding.
* A required artifact (kernel image or headers) is missing.
* A ``v100-workstation`` release omits NVIDIA proprietary modules.
* Any input path uses a forbidden secret-bearing filename.
* Any text-like input contains a detected secret pattern.
* ``release_dir`` resolves into a protected host path.
* ``release_dir`` is non-empty and ``force=False``.

Outputs (all under ``release_dir/``):
* the copied artifacts, at their original relative paths;
* ``MANIFEST.json`` with per-artifact metadata, checks summary, source-lock
  pin status, tool versions, approval state, host checks required, and
  redistribution flags;
* ``SHA256SUMS`` in the standard ``sha256sum`` format;
* optionally ``rollback-notes.md`` when ``ctx.rollback_notes`` is set.

Every artifact carries a ``redistribution`` field of ``"public"`` or
``"restricted"``. NVIDIA proprietary modules and the initramfs that contains
them are marked ``restricted``; the release-level ``distribution_restricted``
flag surfaces this so a publishing workflow can refuse to upload to public
GitHub release assets without license review.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from huey.kernel_build.models import (
    ApprovalState,
    ArtifactKind,
    BuildArtifact,
    Severity,
    ValidationFinding,
)
from huey.kernel_build.policy import PROTECTED_HOST_PATHS
from huey.kernel_build.verifier import VerificationResult

logger = logging.getLogger(__name__)

__all__ = [
    "ReleaseArtifact",
    "ReleaseAssembler",
    "ReleaseContext",
    "ReleaseResult",
]

_MANIFEST_FILENAME = "MANIFEST.json"
_CHECKSUMS_FILENAME = "SHA256SUMS"
_ROLLBACK_NOTES_FILENAME = "rollback-notes.md"
_SCHEMA_VERSION = 1

# ---------------------------------------------------------------------------
# Secret guards
# ---------------------------------------------------------------------------

_FORBIDDEN_FILENAMES = frozenset({
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
    "id_dsa",
    ".env",
    ".netrc",
    ".git-credentials",
    "credentials.json",
})

_FORBIDDEN_EXTENSIONS = frozenset({".priv", ".p12", ".pfx"})

_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"), "PEM private key block"),
    (re.compile(r"\bMOK_PIN\s*=\s*[^\s#]+"), "MOK_PIN assignment"),
    (re.compile(r"\bKBUILD_SIGN_PIN\s*=\s*[^\s#]+"), "KBUILD_SIGN_PIN assignment"),
    (re.compile(r"\bGITHUB_TOKEN\s*=\s*[^\s#]+"), "GITHUB_TOKEN assignment"),
    (re.compile(r"\bAWS_SECRET_ACCESS_KEY\s*=\s*[^\s#]+"), "AWS secret key assignment"),
    (re.compile(r"\bAWS_SESSION_TOKEN\s*=\s*[^\s#]+"), "AWS session token assignment"),
)

_DISTRIBUTION_WARNING = (
    "This release contains NVIDIA proprietary kernel modules and/or an "
    "initramfs that embeds them. Do not publish it to public GitHub release "
    "assets or any public distribution channel without explicit license "
    "review. Distribution is permitted only under the NVIDIA Software "
    "License Agreement for the specific driver version, and only to "
    "recipients who are licensed to receive the driver."
)


# ---------------------------------------------------------------------------
# Context / result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ReleaseContext:
    """All inputs needed to assemble a release.

    ``verification`` must be a completed
    :class:`huey.kernel_build.verifier.VerificationResult` with
    ``boot_ready=True``. A dry-run verification result is refused.

    ``nvidia_modules_dir`` is the staging directory produced by Step 14
    (``<output>/nvidia-<ver>-<kr>/``). Its ``.ko`` files are copied into
    the release under the same directory name.
    """

    release_dir: Path
    kernel_release: str
    driver_version: str
    profile: str
    verification: VerificationResult
    kernel_image_deb: Path
    kernel_headers_deb: Path
    nvidia_modules_dir: Path | None = None
    initramfs: Path | None = None
    config_path: Path | None = None
    source_lock_path: Path | None = None
    tool_versions: dict[str, str] = field(default_factory=dict)
    approval_state: ApprovalState = ApprovalState.PENDING
    rollback_notes: str | None = None
    extra_text_files: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "release_dir", Path(self.release_dir))
        object.__setattr__(self, "kernel_image_deb", Path(self.kernel_image_deb))
        object.__setattr__(self, "kernel_headers_deb", Path(self.kernel_headers_deb))
        for name in ("nvidia_modules_dir", "initramfs", "config_path", "source_lock_path"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, Path(value))
        if isinstance(self.extra_text_files, list):
            object.__setattr__(self, "extra_text_files", tuple(self.extra_text_files))
        else:
            object.__setattr__(
                self, "extra_text_files", tuple(self.extra_text_files or ())
            )


@dataclass(frozen=True, slots=True)
class ReleaseArtifact:
    """A copied release artifact with redistribution and provenance."""

    name: str
    build_artifact: BuildArtifact
    redistribution: str  # "public" | "restricted"
    provenance: str
    _source: Path | None = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.build_artifact.path,
            "kind": self.build_artifact.kind.value,
            "sha256": self.build_artifact.sha256,
            "size_bytes": self.build_artifact.size_bytes,
            "kernel_release": self.build_artifact.kernel_release,
            "redistribution": self.redistribution,
            "provenance": self.provenance,
        }


@dataclass(frozen=True, slots=True)
class ReleaseResult:
    release_dir: Path | None
    manifest_path: Path | None
    checksums_path: Path | None
    artifacts: tuple[ReleaseArtifact, ...]
    approval_state: ApprovalState
    distribution_restricted: bool
    findings: tuple[ValidationFinding, ...]
    dry_run: bool

    def __post_init__(self) -> None:
        if isinstance(self.artifacts, list):
            object.__setattr__(self, "artifacts", tuple(self.artifacts))
        if isinstance(self.findings, list):
            object.__setattr__(self, "findings", tuple(self.findings))

    def has_errors(self) -> bool:
        return any(
            f.severity in (Severity.ERROR, Severity.CRITICAL) for f in self.findings
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_dir": str(self.release_dir) if self.release_dir else None,
            "manifest_path": str(self.manifest_path) if self.manifest_path else None,
            "checksums_path": str(self.checksums_path) if self.checksums_path else None,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "approval_state": self.approval_state.value,
            "distribution_restricted": self.distribution_restricted,
            "findings": [f.to_dict() for f in self.findings],
            "dry_run": self.dry_run,
        }


# ---------------------------------------------------------------------------
# ReleaseAssembler
# ---------------------------------------------------------------------------


class ReleaseAssembler:
    """Assemble a validated release directory."""

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    # ---- public API ------------------------------------------------------

    def build_release(
        self,
        ctx: ReleaseContext,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> ReleaseResult:
        """Assemble ``ctx.release_dir`` and return the manifest summary."""
        pre = self._precheck(ctx)
        if pre is not None:
            return pre

        protected_check = self._check_release_dir(ctx.release_dir)
        if protected_check is not None:
            return protected_check
        # Do not allow cleanup/force to erase the source staging inputs.
        release_root = ctx.release_dir.resolve(strict=False)
        inputs = [ctx.kernel_image_deb, ctx.kernel_headers_deb,
                  ctx.nvidia_modules_dir, ctx.initramfs, ctx.config_path,
                  ctx.source_lock_path, *ctx.extra_text_files]
        for source in inputs:
            if source is None:
                continue
            location = source.resolve(strict=False)
            if location == release_root or release_root in location.parents:
                return self._error_result(
                    code="RELEASE_OVERLAPS_INPUT", message="Release directory overlaps staged input files.",
                    dry_run=dry_run, approval_state=ctx.approval_state,
                )
        # Build the plan without touching the filesystem yet.
        try:
            plan = self._build_plan(ctx)
        except ReleaseAssemblyError as exc:
            return self._error_result(
                code=exc.code, message=str(exc), dry_run=dry_run,
                approval_state=ctx.approval_state,
            )

        # Reject if any forbidden filename or secret was detected while planning.
        if any(
            f.severity in (Severity.ERROR, Severity.CRITICAL) for f in plan["findings"]
        ):
            return ReleaseResult(
                release_dir=None,
                manifest_path=None,
                checksums_path=None,
                artifacts=tuple(plan["artifacts"]),
                approval_state=ctx.approval_state,
                distribution_restricted=plan["distribution_restricted"],
                findings=tuple(plan["findings"]),
                dry_run=dry_run,
            )

        if dry_run:
            plan["findings"].append(
                ValidationFinding(
                    severity=Severity.INFO,
                    code="RELEASE_DRY_RUN",
                    message=(
                        f"Planned: {len(plan['artifacts'])} artifacts into "
                        f"{ctx.release_dir}. No files were written."
                    ),
                )
            )
            return ReleaseResult(
                release_dir=None,
                manifest_path=None,
                checksums_path=None,
                artifacts=tuple(plan["artifacts"]),
                approval_state=ctx.approval_state,
                distribution_restricted=plan["distribution_restricted"],
                findings=tuple(plan["findings"]),
                dry_run=True,
            )

        # Prepare release directory.
        prepare_outcome = self._prepare_release_dir(ctx.release_dir, force=force)
        if prepare_outcome is not None:
            return prepare_outcome

        # Copy artifacts and compute SHA-256 on the copies.
        findings: list[ValidationFinding] = list(plan["findings"])
        copied: list[ReleaseArtifact] = []
        for pending in plan["artifacts"]:
            dest = ctx.release_dir / pending.build_artifact.path
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if pending.build_artifact.kind == ArtifactKind.NVIDIA_MODULE:
                    # Copy the module; do not overwrite if destination is identical.
                    shutil.copy2(pending._source, dest)  # type: ignore[attr-defined]
                else:
                    shutil.copy2(pending._source, dest)  # type: ignore[attr-defined]
            except (OSError, FileNotFoundError) as exc:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="ARTIFACT_COPY_FAILED",
                        message=(
                            f"Could not copy {pending.name} to {dest}: {exc}"
                        ),
                    )
                )
                return ReleaseResult(
                    release_dir=ctx.release_dir,
                    manifest_path=None,
                    checksums_path=None,
                    artifacts=tuple(copied),
                    approval_state=ctx.approval_state,
                    distribution_restricted=plan["distribution_restricted"],
                    findings=tuple(findings),
                    dry_run=False,
                )

            try:
                sha = self._sha256_file(dest)
                size = dest.stat().st_size
            except OSError as exc:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="ARTIFACT_HASH_FAILED",
                        message=f"Could not hash {dest}: {exc}",
                    )
                )
                return ReleaseResult(
                    release_dir=ctx.release_dir,
                    manifest_path=None,
                    checksums_path=None,
                    artifacts=tuple(copied),
                    approval_state=ctx.approval_state,
                    distribution_restricted=plan["distribution_restricted"],
                    findings=tuple(findings),
                    dry_run=False,
                )

            copied.append(
                ReleaseArtifact(
                    name=pending.name,
                    build_artifact=replace(
                        pending.build_artifact,
                        sha256=sha,
                        size_bytes=size,
                    ),
                    redistribution=pending.redistribution,
                    provenance=pending.provenance,
                )
            )

        # Write rollback notes if provided.
        rollback_notes_record: dict[str, Any] | None = None
        if ctx.rollback_notes:
            notes_path = ctx.release_dir / _ROLLBACK_NOTES_FILENAME
            try:
                self._atomic_write_text(notes_path, ctx.rollback_notes + "\n")
                copied.append(
                    ReleaseArtifact(
                        name=_ROLLBACK_NOTES_FILENAME,
                        build_artifact=BuildArtifact(
                            kind=ArtifactKind.MANIFEST,  # reuse; not really a manifest
                            path=_ROLLBACK_NOTES_FILENAME,
                            sha256=self._sha256_file(notes_path),
                            size_bytes=notes_path.stat().st_size,
                            kernel_release=ctx.kernel_release,
                        ),
                        redistribution="public",
                        provenance="operator-notes",
                    )
                )
                rollback_notes_record = {
                    "path": _ROLLBACK_NOTES_FILENAME,
                    "sha256": self._sha256_file(notes_path),
                }
            except OSError as exc:
                findings.append(
                    ValidationFinding(
                        severity=Severity.WARNING,
                        code="ROLLBACK_NOTES_WRITE_FAILED",
                        message=f"Could not write rollback notes: {exc}",
                    )
                )

        # Build manifest.
        manifest_payload = self._manifest_payload(
            ctx=ctx,
            artifacts=copied,
            rollback_notes=rollback_notes_record,
            distribution_restricted=plan["distribution_restricted"],
        )
        manifest_path = ctx.release_dir / _MANIFEST_FILENAME
        try:
            self._atomic_write_text(
                manifest_path,
                json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n",
            )
        except OSError as exc:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="MANIFEST_WRITE_FAILED",
                    message=f"Could not write {manifest_path}: {exc}",
                )
            )
            return ReleaseResult(
                release_dir=ctx.release_dir,
                manifest_path=None,
                checksums_path=None,
                artifacts=tuple(copied),
                approval_state=ctx.approval_state,
                distribution_restricted=plan["distribution_restricted"],
                findings=tuple(findings),
                dry_run=False,
            )

        # SHA256SUMS for everything except the manifest and the checksums file.
        checksums_lines: list[str] = []
        for art in sorted(copied, key=lambda a: a.build_artifact.path):
            checksums_lines.append(
                f"{art.build_artifact.sha256}  {art.build_artifact.path}"
            )
        checksums_path = ctx.release_dir / _CHECKSUMS_FILENAME
        try:
            self._atomic_write_text(
                checksums_path, "\n".join(checksums_lines) + "\n"
            )
        except OSError as exc:
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="CHECKSUMS_WRITE_FAILED",
                    message=f"Could not write {checksums_path}: {exc}",
                )
            )
            checksums_path = None  # type: ignore[assignment]

        if plan["distribution_restricted"]:
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="DISTRIBUTION_RESTRICTED",
                    message=_DISTRIBUTION_WARNING,
                )
            )

        logger.info(
            "release.assembled dir=%s artifacts=%d restricted=%s",
            ctx.release_dir,
            len(copied),
            plan["distribution_restricted"],
        )

        return ReleaseResult(
            release_dir=ctx.release_dir,
            manifest_path=manifest_path,
            checksums_path=checksums_path,
            artifacts=tuple(copied),
            approval_state=ctx.approval_state,
            distribution_restricted=plan["distribution_restricted"],
            findings=tuple(findings),
            dry_run=False,
        )

    # ---- prechecks -------------------------------------------------------

    def _precheck(self, ctx: ReleaseContext) -> ReleaseResult | None:
        if not ctx.verification:
            return self._error_result(
                code="VERIFICATION_MISSING",
                message=(
                    "ReleaseContext.verification is required. Run Step 19's "
                    "ReleaseVerifier first; releases are built only from "
                    "verified artifacts."
                ),
                dry_run=False,
                approval_state=ctx.approval_state,
            )
        if ctx.verification.dry_run:
            return self._error_result(
                code="VERIFICATION_DRY_RUN",
                message=(
                    "A dry-run verification result cannot back a release. "
                    "Re-run ReleaseVerifier without dry_run=True."
                ),
                dry_run=False,
                approval_state=ctx.approval_state,
            )
        if not ctx.verification.boot_ready or ctx.verification.has_errors():
            codes = sorted({f.code for f in ctx.verification.findings})
            return self._error_result(
                code="VERIFICATION_NOT_READY",
                message=(
                    "Verification did not pass (boot_ready=False or "
                    f"ERROR/CRITICAL findings). Codes: {codes}. Fix the "
                    "blocking findings before assembling a release."
                ),
                dry_run=False,
                approval_state=ctx.approval_state,
            )
        # A claimed successful verification does not supersede a missing or
        # unresolved source lock; promotion always requires a genuine pin.
        if ctx.source_lock_path is None:
            return self._error_result(
                code="SOURCE_LOCK_REQUIRED", message="Source lock is required for release assembly.",
                dry_run=False, approval_state=ctx.approval_state,
            )
        from huey.kernel_build.source_manager import SourceLock
        try:
            lock = SourceLock.load_from_path(ctx.source_lock_path)
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            return self._error_result(
                code="SOURCE_LOCK_INVALID", message=f"Source lock cannot be loaded: {exc}",
                dry_run=False, approval_state=ctx.approval_state,
            )
        if lock.status != "pinned" or lock.checksum_sha256 == "0" * 64:
            return self._error_result(
                code="SOURCE_LOCK_UNRESOLVED", message="Source lock is not verified/pinned.",
                dry_run=False, approval_state=ctx.approval_state,
            )
        return None

    def _check_release_dir(self, release_dir: Path) -> ReleaseResult | None:
        try:
            resolved = release_dir.resolve()
        except (OSError, RuntimeError):
            resolved = release_dir
        for protected in PROTECTED_HOST_PATHS:
            try:
                resolved.relative_to(protected)
            except ValueError:
                continue
            return self._error_result(
                code="RELEASE_DIR_PROTECTED",
                message=(
                    f"release_dir resolves inside protected host path "
                    f"{protected!r}: {resolved}"
                ),
                dry_run=False,
                approval_state=ApprovalState.PENDING,
            )
        if resolved == Path("/"):
            return self._error_result(
                code="RELEASE_DIR_PROTECTED",
                message="release_dir must not be the filesystem root.",
                dry_run=False,
                approval_state=ApprovalState.PENDING,
            )
        return None

    def _prepare_release_dir(
        self, release_dir: Path, *, force: bool
    ) -> ReleaseResult | None:
        if release_dir.exists():
            if not release_dir.is_dir():
                return self._error_result(
                    code="RELEASE_DIR_NOT_DIRECTORY",
                    message=f"release_dir exists but is not a directory: {release_dir}",
                    dry_run=False,
                    approval_state=ApprovalState.PENDING,
                )
            try:
                empty = not any(release_dir.iterdir())
            except OSError as exc:
                return self._error_result(
                    code="RELEASE_DIR_UNREADABLE",
                    message=f"Could not inspect {release_dir}: {exc}",
                    dry_run=False,
                    approval_state=ApprovalState.PENDING,
                )
            if not empty:
                if not force:
                    return self._error_result(
                        code="RELEASE_DIR_NOT_EMPTY",
                        message=(
                            f"release_dir is not empty: {release_dir}. Pass "
                            "force=True to overwrite (removes all contents)."
                        ),
                        dry_run=False,
                        approval_state=ApprovalState.PENDING,
                    )
                try:
                    shutil.rmtree(release_dir)
                except OSError as exc:
                    return self._error_result(
                        code="RELEASE_DIR_CLEAR_FAILED",
                        message=f"Could not clear {release_dir}: {exc}",
                        dry_run=False,
                        approval_state=ApprovalState.PENDING,
                    )
        try:
            release_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return self._error_result(
                code="RELEASE_DIR_CREATE_FAILED",
                message=f"Could not create {release_dir}: {exc}",
                dry_run=False,
                approval_state=ApprovalState.PENDING,
            )
        return None

    # ---- planning --------------------------------------------------------

    def _build_plan(self, ctx: ReleaseContext) -> dict[str, Any]:
        findings: list[ValidationFinding] = []
        artifacts: list[ReleaseArtifact] = []
        restricted = False

        def add(
            source: Path,
            *,
            name: str,
            kind: ArtifactKind,
            relpath: str,
            kernel_release: str,
            redistribution: str,
            provenance: str,
        ) -> None:
            nonlocal restricted
            if source.name in _FORBIDDEN_FILENAMES or (
                source.suffix.lower() in _FORBIDDEN_EXTENSIONS
            ):
                raise ReleaseAssemblyError(
                    "FORBIDDEN_FILENAME",
                    f"Refusing to include {source.name!r}: it looks like a "
                    "secret-bearing file.",
                )
            if source.is_symlink():
                raise ReleaseAssemblyError(
                    "ARTIFACT_SYMLINK_REFUSED", "Release artifacts must not be symlinks.",
                )
            if not source.is_file():
                raise ReleaseAssemblyError(
                    "ARTIFACT_MISSING",
                    f"Required artifact not found: {source}",
                )
            if source.suffix.lower() in {
                ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg",
                ".conf", ".ini",
            } or source.suffix == "":
                secret_findings = self._scan_text_file(source)
                findings.extend(secret_findings)
            size = source.stat().st_size
            sha = self._sha256_file(source)
            # Store the source under a private attribute so we can copy later.
            rec = ReleaseArtifact(
                name=name,
                build_artifact=BuildArtifact(
                    kind=kind,
                    path=relpath,
                    sha256=sha,
                    size_bytes=size,
                    kernel_release=kernel_release,
                ),
                redistribution=redistribution,
                provenance=provenance,
            )
            object.__setattr__(rec, "_source", source)  # for the copy step
            if relpath in {_MANIFEST_FILENAME, _CHECKSUMS_FILENAME, _ROLLBACK_NOTES_FILENAME}:
                raise ReleaseAssemblyError(
                    "RESERVED_RELEASE_NAME", f"Reserved release metadata filename: {relpath}",
                )
            if any(existing.build_artifact.path == relpath for existing in artifacts):
                raise ReleaseAssemblyError(
                    "ARTIFACT_PATH_COLLISION", f"Duplicate release path: {relpath}",
                )
            if redistribution == "restricted":
                restricted = True
            artifacts.append(rec)

        # 1. Kernel image .deb
        add(
            ctx.kernel_image_deb,
            name=ctx.kernel_image_deb.name,
            kind=ArtifactKind.KERNEL_IMAGE_DEB,
            relpath=ctx.kernel_image_deb.name,
            kernel_release=ctx.kernel_release,
            redistribution="public",
            provenance="debian-linux-source",
        )
        # 2. Kernel headers .deb
        add(
            ctx.kernel_headers_deb,
            name=ctx.kernel_headers_deb.name,
            kind=ArtifactKind.KERNEL_HEADERS_DEB,
            relpath=ctx.kernel_headers_deb.name,
            kernel_release=ctx.kernel_release,
            redistribution="public",
            provenance="debian-linux-source",
        )

        # 3. NVIDIA modules directory
        if ctx.nvidia_modules_dir is not None:
            if not ctx.nvidia_modules_dir.is_dir():
                raise ReleaseAssemblyError(
                    "NVIDIA_MODULES_DIR_MISSING",
                    f"nvidia_modules_dir not found: {ctx.nvidia_modules_dir}",
                )
            ko_files = sorted(ctx.nvidia_modules_dir.glob("*.ko"))
            if not ko_files:
                raise ReleaseAssemblyError(
                    "NVIDIA_MODULES_EMPTY",
                    f"No .ko files under {ctx.nvidia_modules_dir}",
                )
            subdir = ctx.nvidia_modules_dir.name
            for ko in ko_files:
                add(
                    ko,
                    name=f"{subdir}/{ko.name}",
                    kind=ArtifactKind.NVIDIA_MODULE,
                    relpath=f"{subdir}/{ko.name}",
                    kernel_release=ctx.kernel_release,
                    redistribution="restricted",
                    provenance="nvidia-proprietary",
                )
        elif ctx.profile == "v100-workstation":
            raise ReleaseAssemblyError(
                "NVIDIA_MODULES_REQUIRED",
                "Profile 'v100-workstation' requires nvidia_modules_dir; "
                "missing proprietary modules block release assembly.",
            )

        # 4. Initramfs
        if ctx.initramfs is not None:
            initramfs_restricted = ctx.nvidia_modules_dir is not None
            add(
                ctx.initramfs,
                name=ctx.initramfs.name,
                kind=ArtifactKind.INITRAMFS,
                relpath=ctx.initramfs.name,
                kernel_release=ctx.kernel_release,
                redistribution="restricted" if initramfs_restricted else "public",
                provenance="huey-initramfs",
            )

        # 5. Kernel config
        if ctx.config_path is not None:
            add(
                ctx.config_path,
                name=ctx.config_path.name,
                kind=ArtifactKind.MANIFEST,  # closest existing kind; not a manifest
                relpath=ctx.config_path.name,
                kernel_release=ctx.kernel_release,
                redistribution="public",
                provenance="huey-config",
            )

        # 6. Source lock
        if ctx.source_lock_path is not None:
            add(
                ctx.source_lock_path,
                name=ctx.source_lock_path.name,
                kind=ArtifactKind.MANIFEST,
                relpath=ctx.source_lock_path.name,
                kernel_release=ctx.kernel_release,
                redistribution="public",
                provenance="source-pin",
            )

        # 7. Extra text files (scanned for secrets)
        for extra in ctx.extra_text_files:
            add(
                extra,
                name=extra.name,
                kind=ArtifactKind.MANIFEST,
                relpath=extra.name,
                kernel_release=ctx.kernel_release,
                redistribution="public",
                provenance="operator-supplied",
            )

        # Rollback notes: scan for secrets before we write them.
        if ctx.rollback_notes:
            findings.extend(
                self._scan_text(
                    text=ctx.rollback_notes,
                    source_label=_ROLLBACK_NOTES_FILENAME,
                )
            )

        return {
            "artifacts": artifacts,
            "findings": findings,
            "distribution_restricted": restricted,
        }

    # ---- manifest --------------------------------------------------------

    def _manifest_payload(
        self,
        *,
        ctx: ReleaseContext,
        artifacts: Sequence[ReleaseArtifact],
        rollback_notes: dict[str, Any] | None,
        distribution_restricted: bool,
    ) -> dict[str, Any]:
        verification = ctx.verification
        severities = {s: 0 for s in Severity}
        for f in verification.findings:
            severities[f.severity] += 1

        source_lock: dict[str, Any] | None = None
        if ctx.source_lock_path is not None and ctx.source_lock_path.is_file():
            source_lock = {
                "path": ctx.source_lock_path.name,
                "sha256": self._sha256_file(ctx.source_lock_path),
            }
            try:
                from huey.kernel_build.source_manager import SourceLock
                lock = SourceLock.load_from_path(ctx.source_lock_path)
                source_lock["status"] = lock.status
                source_lock["version"] = lock.version
                source_lock["checksum_sha256"] = lock.checksum_sha256
            except Exception:  # noqa: BLE001
                source_lock["status"] = "unknown"

        return {
            "schema_version": _SCHEMA_VERSION,
            "generated_at": self._clock().astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "kernel_release": ctx.kernel_release,
            "driver_version": ctx.driver_version,
            "profile": ctx.profile,
            "approval_state": ctx.approval_state.value,
            "boot_ready": True,
            "static_checks_passed": verification.static_checks_passed,
            "distribution_restricted": distribution_restricted,
            "distribution_warning": (
                _DISTRIBUTION_WARNING if distribution_restricted else None
            ),
            "host_checks_required": list(verification.host_checks_required),
            "checks_summary": {
                "boot_ready": verification.boot_ready,
                "static_checks_passed": verification.static_checks_passed,
                "errors": severities[Severity.ERROR],
                "critical": severities[Severity.CRITICAL],
                "warnings": severities[Severity.WARNING],
                "infos": severities[Severity.INFO],
                "finding_codes": sorted({f.code for f in verification.findings}),
            },
            "source_lock": source_lock,
            "tool_versions": dict(ctx.tool_versions),
            "rollback_notes": rollback_notes,
            "artifacts": [a.to_dict() for a in artifacts],
        }

    # ---- secret scan -----------------------------------------------------

    def _scan_text_file(self, path: Path) -> list[ValidationFinding]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        return self._scan_text(text=text, source_label=path.name)

    def _scan_text(
        self, *, text: str, source_label: str
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        for pattern, description in _SECRET_PATTERNS:
            m = pattern.search(text)
            if m:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="SECRET_DETECTED",
                        message=(
                            f"{description} detected in {source_label!r}. "
                            "Remove the secret before assembling a release."
                        ),
                        context={
                            "source": source_label,
                            "pattern": description,
                            "snippet": m.group(0)[:12] + "…"
                            if len(m.group(0)) > 12
                            else m.group(0),
                        },
                    )
                )
        return findings

    # ---- atomic writes ---------------------------------------------------

    @staticmethod
    def _atomic_write_text(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            dir=str(path.parent), prefix=path.name + ".", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(text)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    @staticmethod
    def _sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _error_result(
        *,
        code: str,
        message: str,
        dry_run: bool,
        approval_state: ApprovalState,
    ) -> ReleaseResult:
        return ReleaseResult(
            release_dir=None,
            manifest_path=None,
            checksums_path=None,
            artifacts=(),
            approval_state=approval_state,
            distribution_restricted=False,
            findings=(
                ValidationFinding(
                    severity=Severity.ERROR, code=code, message=message
                ),
            ),
            dry_run=dry_run,
        )


# ---------------------------------------------------------------------------
# Internal exception (not exported)
# ---------------------------------------------------------------------------


class ReleaseAssemblyError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
