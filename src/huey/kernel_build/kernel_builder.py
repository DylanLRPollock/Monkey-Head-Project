"""Non-root kernel compilation for the HueyOS kernel build framework.

Runs against a pinned kernel source tree and the effective ``.config``
produced by :mod:`huey.kernel_build.config_builder`:

1. Initializes an isolated objtree and copies the config into place.
2. Runs ``make O=<objtree> olddefconfig`` (prepares ``include/config`` so
   the release target and kbuild can proceed).
3. Runs ``make O=<objtree> -s kernelrelease`` to capture the exact
   ``KERNELRELEASE`` for this build. The value recorded is authoritative
   for matching later stages (NVIDIA build, initramfs build, verification).
4. Runs ``make -jN O=<objtree> bindeb-pkg`` with reproducibility variables
   (``SOURCE_DATE_EPOCH``, ``KBUILD_BUILD_TIMESTAMP``, ``KBUILD_BUILD_USER``,
   ``KBUILD_BUILD_HOST``) and the requested ``LOCALVERSION`` /
   ``KDEB_PKGVERSION``.
5. Discovers the produced ``.deb`` files under the isolated build directory
   and classifies them by their ``Package:`` field (queried via
   ``dpkg-deb --field``). The build **requires** a ``linux-image-<kr>`` and
   a ``linux-headers-<kr>`` package; any mismatch is a blocking finding.
6. Computes SHA-256 and size for the required artifacts.

Non-goals
---------
* Never runs ``dpkg -i``, ``dkms install``, ``update-initramfs``,
  ``update-grub``, or modifies ``/boot``, ``/lib/modules``, or ``/etc``.
* Never assumes a ``.deb`` filename pattern; only the ``Package:`` field is
  authoritative. This makes the builder robust against ``KDEB_PKGVERSION``
  and version-string variations.
* Never requires root; the caller's uid is not inspected, but no privileged
  operation is attempted.
"""

from __future__ import annotations

import hashlib
import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from huey.kernel_build.models import (
    ArtifactKind,
    BuildArtifact,
    Severity,
    ValidationFinding,
)
from huey.kernel_build.policy import check_path_destination_safe
from huey.kernel_build.runner import (
    CommandSpec,
    RunnerError,
    RunnerProtocol,
    RunnerTimeout,
)

logger = logging.getLogger(__name__)

__all__ = [
    "KernelBuildResult",
    "KernelBuilder",
]

#: Minimum safe jobs; guards against accidental single-job or zero-job builds.
_MIN_JOBS = 1

#: bindeb-pkg routinely takes 20-90 minutes on 16 GiB hosts at -j4.
_BINDEB_TIMEOUT_SECONDS: float = 3 * 3600.0
_OLDDEFCONFIG_TIMEOUT_SECONDS: float = 15 * 60.0
_KERNELRELEASE_TIMEOUT_SECONDS: float = 2 * 60.0
_DPKG_DEB_TIMEOUT_SECONDS: float = 30.0


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class KernelBuildResult:
    """Outcome of a kernel build attempt.

    ``kernel_release`` is ``None`` when the build did not reach
    ``make -s kernelrelease`` (dry run, or precondition failure).
    """

    kernel_release: str | None
    localversion: str
    kdeb_pkgversion: str | None
    jobs: int
    source_date_epoch: int
    image_deb: BuildArtifact | None
    headers_deb: BuildArtifact | None
    findings: tuple[ValidationFinding, ...]
    dry_run: bool

    def __post_init__(self) -> None:
        if isinstance(self.findings, list):
            object.__setattr__(self, "findings", tuple(self.findings))

    def has_errors(self) -> bool:
        return any(
            f.severity in (Severity.ERROR, Severity.CRITICAL) for f in self.findings
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kernel_release": self.kernel_release,
            "localversion": self.localversion,
            "kdeb_pkgversion": self.kdeb_pkgversion,
            "jobs": self.jobs,
            "source_date_epoch": self.source_date_epoch,
            "image_deb": self.image_deb.to_dict() if self.image_deb else None,
            "headers_deb": self.headers_deb.to_dict() if self.headers_deb else None,
            "findings": [f.to_dict() for f in self.findings],
            "dry_run": self.dry_run,
        }


# ---------------------------------------------------------------------------
# KernelBuilder
# ---------------------------------------------------------------------------


class KernelBuilder:
    """Build Debian kernel packages from a pinned source tree.

    All subprocess execution flows through the injected
    :class:`huey.kernel_build.runner.RunnerProtocol`, so tests can substitute
    a fake runner without launching ``make`` or ``dpkg-deb``.
    """

    def __init__(self, runner: RunnerProtocol) -> None:
        self._runner = runner

    # ---- public API ------------------------------------------------------

    def build(
        self,
        source_dir: Path,
        config_path: Path,
        output_dir: Path,
        *,
        localversion: str = "-huey1",
        jobs: int = 4,
        kdeb_pkgversion: str | None = None,
        source_date_epoch: int = 0,
        dry_run: bool = False,
        workspace_root: Path | None = None,
    ) -> KernelBuildResult:
        """Build the kernel and its headers as ``.deb`` packages.

        Parameters
        ----------
        source_dir:
            Extracted kernel source tree with ``Makefile``.
        config_path:
            Effective ``.config`` (typically produced by
            :class:`~huey.kernel_build.config_builder.ConfigBuilder`).
        output_dir:
            Destination root. ``output_dir/build/kernel-tree`` is used as the
            objtree; ``.deb`` files are written under ``output_dir/build``.
        localversion:
            Kernel ``LOCALVERSION`` suffix (must start with ``-`` or be empty).
        jobs:
            ``make -jN`` value. Minimum 1, do not pass ``os.cpu_count()``
            blindly: the host has 16 GiB RAM and must remain responsive.
        kdeb_pkgversion:
            Optional ``KDEB_PKGVERSION`` override. When omitted, the kernel
            uses its default derived from ``KERNELRELEASE``.
        source_date_epoch:
            Reproducible-build timestamp. ``0`` produces the Unix epoch.
        dry_run:
            When ``True``, performs no I/O and launches no subprocess.

        Returns
        -------
        KernelBuildResult
            Always returned; check :meth:`KernelBuildResult.has_errors`.
        """
        source_dir = Path(source_dir).resolve()
        config_path = Path(config_path).resolve()
        output_dir = Path(output_dir)
        if workspace_root is not None and not output_dir.is_absolute():
            output_dir = Path(workspace_root) / output_dir
        output_dir = output_dir.resolve()
        build_dir = output_dir / "build"
        objtree = build_dir / "kernel-tree"

        # Reject live host destinations and accidental source/input overwrites.
        blocked = check_path_destination_safe(output_dir, workspace_root=workspace_root)
        if blocked:
            return self._error_result(
                localversion=localversion, jobs=jobs if type(jobs) is int else 0,
                kdeb_pkgversion=kdeb_pkgversion,
                source_date_epoch=source_date_epoch,
                code=blocked[0].code, message=blocked[0].message,
            )
        if (output_dir == source_dir or output_dir in source_dir.parents
                or source_dir in output_dir.parents):
            return self._error_result(
                localversion=localversion, jobs=jobs if type(jobs) is int else 0,
                kdeb_pkgversion=kdeb_pkgversion,
                source_date_epoch=source_date_epoch,
                code="UNSAFE_OUTPUT_OVERLAP",
                message="Kernel output must be separate from the source tree.",
            )
        if config_path == objtree / ".config" or config_path == build_dir / ".config":
            return self._error_result(
                localversion=localversion, jobs=jobs if type(jobs) is int else 0,
                kdeb_pkgversion=kdeb_pkgversion,
                source_date_epoch=source_date_epoch,
                code="OUTPUT_OVERWRITES_CONFIG",
                message="Kernel output would overwrite the supplied config file.",
            )
        if kdeb_pkgversion is not None and not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9.+~:-]*", kdeb_pkgversion,
        ):
            return self._error_result(
                localversion=localversion, jobs=jobs if type(jobs) is int else 0,
                kdeb_pkgversion=kdeb_pkgversion,
                source_date_epoch=source_date_epoch,
                code="INVALID_KDEB_PKGVERSION",
                message="KDEB_PKGVERSION must be a safe Debian version string.",
            )
        validation = self._validate_inputs(
            source_dir=source_dir,
            config_path=config_path,
            jobs=jobs,
            localversion=localversion,
            source_date_epoch=source_date_epoch,
        )
        if validation is not None:
            return validation

        if dry_run:
            return self._dry_run_result(
                source_dir=source_dir,
                config_path=config_path,
                output_dir=output_dir,
                objtree=objtree,
                localversion=localversion,
                jobs=jobs,
                kdeb_pkgversion=kdeb_pkgversion,
                source_date_epoch=source_date_epoch,
            )

        # Never copy a config through a symlink outside the isolated objtree.
        if (objtree.is_symlink() or (objtree / ".config").is_symlink()
                or build_dir.is_symlink()):
            return self._error_result(
                localversion=localversion, jobs=jobs,
                kdeb_pkgversion=kdeb_pkgversion,
                source_date_epoch=source_date_epoch,
                code="SYMLINKED_BUILD_OUTPUT",
                message="Kernel objtree contains an unsafe output symlink.",
            )

        # ---- prepare objtree ------------------------------------------------
        try:
            build_dir.mkdir(parents=True, exist_ok=True)
            objtree.mkdir(parents=True, exist_ok=True)
            shutil.copy2(config_path, objtree / ".config")
        except OSError as exc:
            return self._error_result(
                localversion=localversion,
                jobs=jobs,
                kdeb_pkgversion=kdeb_pkgversion,
                source_date_epoch=source_date_epoch,
                code="OBJTREE_PREPARE_FAILED",
                message=f"Could not prepare objtree {objtree}: {exc}",
            )

        # Remove stale .debs so discovery sees only this run's outputs.
        for stale in build_dir.glob("*.deb"):
            try:
                stale.unlink()
            except OSError as exc:
                return self._error_result(
                    localversion=localversion,
                    jobs=jobs,
                    kdeb_pkgversion=kdeb_pkgversion,
                    source_date_epoch=source_date_epoch,
                    code="STALE_DEB_UNLINK_FAILED",
                    message=f"Could not remove stale {stale}: {exc}",
                )

        env = self._make_env(
            localversion=localversion,
            kdeb_pkgversion=kdeb_pkgversion,
            source_date_epoch=source_date_epoch,
        )

        # ---- make olddefconfig ---------------------------------------------
        prep = self._run_olddefconfig(source_dir, objtree, env)
        if isinstance(prep, KernelBuildResult):
            return prep

        # ---- make -s kernelrelease -----------------------------------------
        kr_outcome = self._run_kernelrelease(source_dir, objtree, env)
        if isinstance(kr_outcome, KernelBuildResult):
            return kr_outcome
        kernel_release = kr_outcome
        if localversion and not kernel_release.endswith(localversion):
            # Not fatal: kernelrelease may not reflect LOCALVERSION if the
            # caller passed a value that the Makefile rejected. Record it as
            # a WARNING; the mismatch will also surface when matching .deb
            # package names against the reported release.
            pass  # downgraded to a finding added after successful build

        # ---- make -jN bindeb-pkg -------------------------------------------
        bindeb_outcome = self._run_bindeb(source_dir, objtree, env, jobs)
        if isinstance(bindeb_outcome, KernelBuildResult):
            return bindeb_outcome

        # ---- discover .debs ------------------------------------------------
        candidates = sorted(build_dir.rglob("*.deb"))
        if not candidates:
            return self._error_result(
                localversion=localversion,
                jobs=jobs,
                kdeb_pkgversion=kdeb_pkgversion,
                source_date_epoch=source_date_epoch,
                code="NO_DEBS_FOUND",
                message=(
                    f"bindeb-pkg completed but no .deb files were found under "
                    f"{build_dir}. Expected linux-image-<kr>_*.deb and "
                    f"linux-headers-<kr>_*.deb."
                ),
            )

        findings: list[ValidationFinding] = []

        image_deb: BuildArtifact | None = None
        headers_deb: BuildArtifact | None = None
        other_deb_names: list[str] = []
        expected_image_pkg = f"linux-image-{kernel_release}"
        expected_headers_pkg = f"linux-headers-{kernel_release}"

        for deb_path in candidates:
            package_name = self._query_package_field(deb_path)
            if package_name is None:
                findings.append(
                    ValidationFinding(
                        severity=Severity.WARNING,
                        code="DEB_PACKAGE_FIELD_UNAVAILABLE",
                        message=(
                            f"Could not query Package field of "
                            f"{deb_path.name}; skipping classification."
                        ),
                        context={"path": str(deb_path)},
                    )
                )
                continue

            if package_name == expected_image_pkg:
                artifact = self._artifact_from_deb(
                    deb_path, output_dir, kernel_release,
                    ArtifactKind.KERNEL_IMAGE_DEB,
                )
                if artifact is None:
                    findings.append(
                        ValidationFinding(
                            severity=Severity.ERROR,
                            code="ARTIFACT_PATH_INVALID",
                            message=(
                                f"Image .deb {deb_path.name} cannot be "
                                "represented as a build artifact (path escape "
                                "or I/O error)."
                            ),
                        )
                    )
                else:
                    image_deb = artifact
            elif package_name == expected_headers_pkg:
                artifact = self._artifact_from_deb(
                    deb_path, output_dir, kernel_release,
                    ArtifactKind.KERNEL_HEADERS_DEB,
                )
                if artifact is None:
                    findings.append(
                        ValidationFinding(
                            severity=Severity.ERROR,
                            code="ARTIFACT_PATH_INVALID",
                            message=(
                                f"Headers .deb {deb_path.name} cannot be "
                                "represented as a build artifact (path escape "
                                "or I/O error)."
                            ),
                        )
                    )
                else:
                    headers_deb = artifact
            else:
                other_deb_names.append(f"{package_name} ({deb_path.name})")

        if image_deb is None:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="IMAGE_DEB_MISSING",
                    message=(
                        f"No .deb with Package == {expected_image_pkg!r} was "
                        f"found among {[c.name for c in candidates]!r}. "
                        "A matching linux-image package is required."
                    ),
                    context={
                        "expected_package": expected_image_pkg,
                        "candidates": [c.name for c in candidates],
                    },
                )
            )
        if headers_deb is None:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="HEADERS_DEB_MISSING",
                    message=(
                        f"No .deb with Package == {expected_headers_pkg!r} "
                        f"was found among {[c.name for c in candidates]!r}. "
                        "Matching headers are required for the NVIDIA module "
                        "build."
                    ),
                    context={
                        "expected_package": expected_headers_pkg,
                        "candidates": [c.name for c in candidates],
                    },
                )
            )

        if localversion and not kernel_release.endswith(localversion):
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="LOCALVERSION_NOT_IN_KERNELRELEASE",
                    message=(
                        f"Requested LOCALVERSION={localversion!r} does not "
                        f"appear as a suffix of kernel_release="
                        f"{kernel_release!r}. Verify the Makefile accepts the "
                        "value; module version matching may be affected."
                    ),
                    context={
                        "localversion": localversion,
                        "kernel_release": kernel_release,
                    },
                )
            )

        if other_deb_names:
            findings.append(
                ValidationFinding(
                    severity=Severity.INFO,
                    code="OTHER_DEBS_PRESENT",
                    message=(
                        "Additional .deb packages were produced and are not "
                        "included as required artifacts (they may still be "
                        "useful, e.g. linux-libc-dev or *-dbg)."
                    ),
                    context={"other_debs": other_deb_names},
                )
            )

        logger.info(
            "kernel.build complete kernel_release=%s image=%s headers=%s "
            "errors=%d",
            kernel_release,
            image_deb.path if image_deb else None,
            headers_deb.path if headers_deb else None,
            sum(1 for f in findings if f.severity in (Severity.ERROR, Severity.CRITICAL)),
        )

        return KernelBuildResult(
            kernel_release=kernel_release,
            localversion=localversion,
            kdeb_pkgversion=kdeb_pkgversion,
            jobs=jobs,
            source_date_epoch=source_date_epoch,
            image_deb=image_deb,
            headers_deb=headers_deb,
            findings=tuple(findings),
            dry_run=False,
        )

    # ---- internals -------------------------------------------------------

    def _validate_inputs(
        self,
        *,
        source_dir: Path,
        config_path: Path,
        jobs: int,
        localversion: str,
        source_date_epoch: int,
    ) -> KernelBuildResult | None:
        if not (source_dir / "Makefile").is_file():
            return self._error_result(
                localversion=localversion, jobs=jobs,
                kdeb_pkgversion=None, source_date_epoch=source_date_epoch,
                code="SOURCE_MISSING_MAKEFILE",
                message=f"Kernel source has no Makefile: {source_dir}",
            )
        if not config_path.is_file():
            return self._error_result(
                localversion=localversion, jobs=jobs,
                kdeb_pkgversion=None, source_date_epoch=source_date_epoch,
                code="CONFIG_MISSING",
                message=f"Effective .config missing: {config_path}",
            )
        if type(jobs) is not int or jobs < _MIN_JOBS:
            return self._error_result(
                localversion=localversion, jobs=jobs if type(jobs) is int else 0,
                kdeb_pkgversion=None, source_date_epoch=source_date_epoch,
                code="INVALID_JOBS",
                message=f"jobs must be an int >= {_MIN_JOBS}, got {jobs!r}",
            )
        if not isinstance(localversion, str) or (localversion and not re.fullmatch(r"-[A-Za-z0-9][A-Za-z0-9._+~-]*", localversion)):
            return self._error_result(
                localversion=localversion, jobs=jobs,
                kdeb_pkgversion=None, source_date_epoch=source_date_epoch,
                code="INVALID_LOCALVERSION",
                message=(
                    f"localversion must be empty or start with '-', got "
                    f"{localversion!r}"
                ),
            )
        if type(source_date_epoch) is not int or source_date_epoch < 0:
            return self._error_result(
                localversion=localversion, jobs=jobs,
                kdeb_pkgversion=None, source_date_epoch=source_date_epoch,
                code="INVALID_SOURCE_DATE_EPOCH",
                message=(
                    f"source_date_epoch must be a non-negative int, got "
                    f"{source_date_epoch!r}"
                ),
            )
        return None

    @staticmethod
    def _make_env(
        *,
        localversion: str,
        kdeb_pkgversion: str | None,
        source_date_epoch: int,
    ) -> dict[str, str]:
        env = {
            "LOCALVERSION": localversion,
            "SOURCE_DATE_EPOCH": str(source_date_epoch),
            "KBUILD_BUILD_TIMESTAMP": "Thu, 01 Jan 1970 00:00:00 +0000",
            "KBUILD_BUILD_USER": "huey",
            "KBUILD_BUILD_HOST": "huey-builder",
        }
        if kdeb_pkgversion:
            env["KDEB_PKGVERSION"] = kdeb_pkgversion
        return env

    def _run_olddefconfig(
        self, source_dir: Path, objtree: Path, env: dict[str, str]
    ) -> KernelBuildResult | str:
        spec = CommandSpec(
            argv=("make", f"O={objtree}", "olddefconfig"),
            cwd=source_dir,
            description="make olddefconfig (kernel_builder)",
            timeout_seconds=_OLDDEFCONFIG_TIMEOUT_SECONDS,
            env_overrides=env,
        )
        try:
            result = self._runner.run(spec)
        except RunnerTimeout as exc:
            return self._error_result(
                localversion=env["LOCALVERSION"], jobs=1,
                kdeb_pkgversion=env.get("KDEB_PKGVERSION"),
                source_date_epoch=int(env["SOURCE_DATE_EPOCH"]),
                code="OLDDEFCONFIG_TIMEOUT",
                message=f"make olddefconfig timed out: {exc}",
            )
        except RunnerError as exc:
            return self._error_result(
                localversion=env["LOCALVERSION"], jobs=1,
                kdeb_pkgversion=env.get("KDEB_PKGVERSION"),
                source_date_epoch=int(env["SOURCE_DATE_EPOCH"]),
                code="OLDDEFCONFIG_LAUNCH_FAILED",
                message=f"make olddefconfig could not launch: {exc}",
            )
        if not result.succeeded:
            return self._error_result(
                localversion=env["LOCALVERSION"], jobs=1,
                kdeb_pkgversion=env.get("KDEB_PKGVERSION"),
                source_date_epoch=int(env["SOURCE_DATE_EPOCH"]),
                code="OLDDEFCONFIG_FAILED",
                message=(
                    f"make olddefconfig exited "
                    f"{result.command.returncode}"
                ),
            )
        return "ok"

    def _run_kernelrelease(
        self, source_dir: Path, objtree: Path, env: dict[str, str]
    ) -> KernelBuildResult | str:
        spec = CommandSpec(
            argv=("make", f"O={objtree}", "-s", "kernelrelease"),
            cwd=source_dir,
            description="make -s kernelrelease",
            timeout_seconds=_KERNELRELEASE_TIMEOUT_SECONDS,
            env_overrides=env,
        )
        try:
            result = self._runner.run(spec)
        except RunnerTimeout as exc:
            return self._error_result(
                localversion=env["LOCALVERSION"], jobs=1,
                kdeb_pkgversion=env.get("KDEB_PKGVERSION"),
                source_date_epoch=int(env["SOURCE_DATE_EPOCH"]),
                code="KERNELRELEASE_TIMEOUT",
                message=f"make -s kernelrelease timed out: {exc}",
            )
        except RunnerError as exc:
            return self._error_result(
                localversion=env["LOCALVERSION"], jobs=1,
                kdeb_pkgversion=env.get("KDEB_PKGVERSION"),
                source_date_epoch=int(env["SOURCE_DATE_EPOCH"]),
                code="KERNELRELEASE_LAUNCH_FAILED",
                message=f"make -s kernelrelease could not launch: {exc}",
            )
        if not result.succeeded:
            return self._error_result(
                localversion=env["LOCALVERSION"], jobs=1,
                kdeb_pkgversion=env.get("KDEB_PKGVERSION"),
                source_date_epoch=int(env["SOURCE_DATE_EPOCH"]),
                code="KERNELRELEASE_FAILED",
                message=(
                    f"make -s kernelrelease exited "
                    f"{result.command.returncode}"
                ),
            )
        stdout = (result.stdout or b"").decode("utf-8", errors="replace")
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        if not lines:
            return self._error_result(
                localversion=env["LOCALVERSION"], jobs=1,
                kdeb_pkgversion=env.get("KDEB_PKGVERSION"),
                source_date_epoch=int(env["SOURCE_DATE_EPOCH"]),
                code="KERNELRELEASE_EMPTY",
                message=(
                    "make -s kernelrelease produced no output; cannot "
                    "determine target KERNELRELEASE."
                ),
            )
        release = lines[-1]
        if len(lines) != 1 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+~-]*", release):
            return self._error_result(
                localversion=env["LOCALVERSION"], jobs=1,
                kdeb_pkgversion=env.get("KDEB_PKGVERSION"),
                source_date_epoch=int(env["SOURCE_DATE_EPOCH"]),
                code="KERNELRELEASE_INVALID",
                message="Kernel release output must be a single valid token.",
            )
        return release

    def _run_bindeb(
        self, source_dir: Path, objtree: Path, env: dict[str, str], jobs: int
    ) -> KernelBuildResult | str:
        spec = CommandSpec(
            argv=("make", f"-j{jobs}", f"O={objtree}", "bindeb-pkg"),
            cwd=source_dir,
            description=f"make -j{jobs} bindeb-pkg",
            timeout_seconds=_BINDEB_TIMEOUT_SECONDS,
            env_overrides=env,
        )
        try:
            result = self._runner.run(spec)
        except RunnerTimeout as exc:
            return self._error_result(
                localversion=env["LOCALVERSION"], jobs=jobs,
                kdeb_pkgversion=env.get("KDEB_PKGVERSION"),
                source_date_epoch=int(env["SOURCE_DATE_EPOCH"]),
                code="BINDEB_TIMEOUT",
                message=f"make bindeb-pkg timed out: {exc}",
            )
        except RunnerError as exc:
            return self._error_result(
                localversion=env["LOCALVERSION"], jobs=jobs,
                kdeb_pkgversion=env.get("KDEB_PKGVERSION"),
                source_date_epoch=int(env["SOURCE_DATE_EPOCH"]),
                code="BINDEB_LAUNCH_FAILED",
                message=f"make bindeb-pkg could not launch: {exc}",
            )
        if not result.succeeded:
            return self._error_result(
                localversion=env["LOCALVERSION"], jobs=jobs,
                kdeb_pkgversion=env.get("KDEB_PKGVERSION"),
                source_date_epoch=int(env["SOURCE_DATE_EPOCH"]),
                code="BINDEB_FAILED",
                message=(
                    f"make bindeb-pkg exited "
                    f"{result.command.returncode}"
                ),
            )
        return "ok"

    def _query_package_field(self, deb_path: Path) -> str | None:
        """Query ``dpkg-deb --field <deb> Package`` and return the value."""
        spec = CommandSpec(
            argv=("dpkg-deb", "--field", str(deb_path), "Package"),
            cwd=deb_path.parent,
            description=f"dpkg-deb Package for {deb_path.name}",
            timeout_seconds=_DPKG_DEB_TIMEOUT_SECONDS,
        )
        try:
            result = self._runner.run(spec)
        except (RunnerError, RunnerTimeout):
            return None
        if not result.succeeded or not result.stdout:
            return None
        text = result.stdout.decode("utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("Package:"):
                value = line.split(":", 1)[1].strip()
                return value or None
        return None

    @staticmethod
    def _sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _artifact_from_deb(
        self,
        deb_path: Path,
        output_dir: Path,
        kernel_release: str,
        kind: ArtifactKind,
    ) -> BuildArtifact | None:
        try:
            rel = deb_path.resolve().relative_to(output_dir)
        except (ValueError, OSError):
            return None
        if rel.is_absolute() or ".." in rel.parts:
            return None
        try:
            sha = self._sha256_file(deb_path)
            size = deb_path.stat().st_size
        except OSError:
            return None
        return BuildArtifact(
            kind=kind,
            path=str(rel),
            sha256=sha,
            size_bytes=size,
            kernel_release=kernel_release,
        )

    @staticmethod
    def _error_result(
        *,
        localversion: str,
        jobs: int,
        kdeb_pkgversion: str | None,
        source_date_epoch: int,
        code: str,
        message: str,
    ) -> KernelBuildResult:
        return KernelBuildResult(
            kernel_release=None,
            localversion=localversion,
            kdeb_pkgversion=kdeb_pkgversion,
            jobs=jobs,
            source_date_epoch=source_date_epoch,
            image_deb=None,
            headers_deb=None,
            findings=(
                ValidationFinding(
                    severity=Severity.ERROR, code=code, message=message
                ),
            ),
            dry_run=False,
        )

    @staticmethod
    def _dry_run_result(
        *,
        source_dir: Path,
        config_path: Path,
        output_dir: Path,
        objtree: Path,
        localversion: str,
        jobs: int,
        kdeb_pkgversion: str | None,
        source_date_epoch: int,
    ) -> KernelBuildResult:
        return KernelBuildResult(
            kernel_release=None,
            localversion=localversion,
            kdeb_pkgversion=kdeb_pkgversion,
            jobs=jobs,
            source_date_epoch=source_date_epoch,
            image_deb=None,
            headers_deb=None,
            findings=(
                ValidationFinding(
                    severity=Severity.INFO,
                    code="KERNEL_BUILD_DRY_RUN",
                    message=(
                        "Planned: make olddefconfig, make -s kernelrelease, "
                        f"make -j{jobs} bindeb-pkg in {objtree}. No files "
                        "were written and no subprocess was launched."
                    ),
                    context={
                        "source_dir": str(source_dir),
                        "config_path": str(config_path),
                        "output_dir": str(output_dir),
                        "objtree": str(objtree),
                        "localversion": localversion,
                        "jobs": jobs,
                        "kdeb_pkgversion": kdeb_pkgversion,
                        "source_date_epoch": source_date_epoch,
                    },
                ),
            ),
            dry_run=True,
        )
