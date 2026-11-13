"""Proprietary NVIDIA 580.196.07 module builder for the HueyOS kernel builder.

Scope
-----
Discover a verified local DKMS source tree for the proprietary R580 driver,
build the kernel modules for the **exact** target ``KERNELRELEASE`` against
matching headers, stage the resulting ``.ko`` files under a private output
directory, and verify:

* ``vermagic`` contains the target kernel release exactly;
* ``modinfo -F version`` reports the pinned driver version;
* the module flavor is ``proprietary`` (the open modules do not support
  Volta ``sm_70``; R580 is the last branch that does);
* Secure Boot signing state, if enabled, is recorded without attempting to
  sign here (signing is a separate phase, Step 18).

What this module does **not** do
---------------------------------
* Never runs the vendor ``.run`` installer against the live OS.
* Never runs ``dkms install``, ``dpkg -i``, ``update-initramfs``,
  ``update-grub``, or writes outside ``output_dir``.
* Never patches vendor source silently. A required patch must be committed as
  a separate reviewed change with provenance.
* Never requires root; the caller is expected to run as a non-root build user.

Source discovery
----------------
Priority order:

1. ``dkms_source_dir`` passed by the caller (verified to contain a
   ``dkms.conf`` and a ``Makefile``/``Kbuild``).
2. Default DKMS source roots under ``/var/lib/dkms/nvidia/<version>/source``
   and ``/usr/src/nvidia-<version>`` are *candidates* only; the caller must
   pass ``allow_system_dkms_discovery=True`` to use them.

This keeps a build deterministic: the framework never silently picks a
system DKMS tree the caller did not acknowledge.
"""

from __future__ import annotations

import hashlib
import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from huey.kernel_build.models import (
    ArtifactKind,
    BuildArtifact,
    ModuleFlavor,
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
    "NvidiaBuildResult",
    "NvidiaBuilder",
    "REQUIRED_MODULES",
]

#: Modules staged by the builder. ``nvidia`` and ``nvidia-uvm`` are required
#: for compute; ``nvidia-modeset`` and ``nvidia-drm`` are optional and are
#: staged when present (they are required only when the GPU drives a display,
#: which the V100 does not).
REQUIRED_MODULES: tuple[str, ...] = ("nvidia", "nvidia-uvm")
OPTIONAL_MODULES: tuple[str, ...] = ("nvidia-modeset", "nvidia-drm")

_VERMAGIC_TIMEOUT_SECONDS: float = 30.0
_MODINFO_TIMEOUT_SECONDS: float = 30.0
_DKMS_BUILD_TIMEOUT_SECONDS: float = 3600.0

#: Default DKMS source roots when discovery is explicitly permitted.
_DEFAULT_DKMS_SOURCE_ROOTS: tuple[str, ...] = (
    "/var/lib/dkms/nvidia/{version}/source",
    "/usr/src/nvidia-{version}",
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NvidiaBuildResult:
    """Outcome of an NVIDIA module build attempt.

    ``module_artifacts`` maps module name (without ``.ko`` suffix) to a
    :class:`BuildArtifact` with a workspace-relative path.
    """

    kernel_release: str | None
    driver_version: str
    module_flavor: ModuleFlavor
    source_dir: Path | None
    module_artifacts: dict[str, BuildArtifact]
    findings: tuple[ValidationFinding, ...]
    dry_run: bool

    def __post_init__(self) -> None:
        if isinstance(self.module_artifacts, dict) is False:
            raise TypeError("NvidiaBuildResult.module_artifacts must be a dict")
        if isinstance(self.findings, list):
            object.__setattr__(self, "findings", tuple(self.findings))

    def has_errors(self) -> bool:
        return any(
            f.severity in (Severity.ERROR, Severity.CRITICAL) for f in self.findings
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kernel_release": self.kernel_release,
            "driver_version": self.driver_version,
            "module_flavor": self.module_flavor.value,
            "source_dir": str(self.source_dir) if self.source_dir else None,
            "module_artifacts": {
                name: art.to_dict() for name, art in self.module_artifacts.items()
            },
            "findings": [f.to_dict() for f in self.findings],
            "dry_run": self.dry_run,
        }


# ---------------------------------------------------------------------------
# NvidiaBuilder
# ---------------------------------------------------------------------------


class NvidiaBuilder:
    """Build the proprietary NVIDIA kernel modules for a target release."""

    def __init__(self, runner: RunnerProtocol) -> None:
        self._runner = runner

    # ---- public API ------------------------------------------------------

    def build(
        self,
        *,
        kernel_release: str,
        driver_version: str,
        module_flavor: ModuleFlavor,
        headers_dir: Path,
        output_dir: Path,
        dkms_source_dir: Path | None = None,
        allow_system_dkms_discovery: bool = False,
        secure_boot_enabled: bool = False,
        dry_run: bool = False,
        workspace_root: Path | None = None,
    ) -> NvidiaBuildResult:
        """Build the proprietary NVIDIA modules for ``kernel_release``.

        Parameters
        ----------
        kernel_release:
            Exact target ``KERNELRELEASE`` (from Step 12's
            ``make -s kernelrelease``). Must not be empty.
        driver_version:
            Pinned NVIDIA driver version (e.g. ``"580.196.07"``). Must be
            non-empty and match the discovered source.
        module_flavor:
            Must be :attr:`ModuleFlavor.PROPRIETARY` when the target profile
            is Volta ``sm_70``. The open flavor is rejected here; the profile
            check is duplicated from :mod:`huey.kernel_build.policy` so that a
            direct call cannot bypass it.
        headers_dir:
            Directory containing ``include/generated`` and a ``Makefile`` for
            the **exact** target kernel release. Typically the ``-headers``
            tree from Step 12, or ``/lib/modules/<kr>/build``.
        output_dir:
            Staging directory. The builder writes under
            ``output_dir/nvidia-<driver_version>-<kernel_release>/`` and
            nothing else.
        dkms_source_dir:
            Explicit DKMS source tree (contains ``dkms.conf`` and
            ``Makefile``/``Kbuild``). Preferred over system discovery.
        allow_system_dkms_discovery:
            When ``True``, falls back to ``/var/lib/dkms/nvidia/<ver>/source``
            and ``/usr/src/nvidia-<ver>`` if ``dkms_source_dir`` is not
            supplied. Defaults to ``False``.
        secure_boot_enabled:
            Recorded for the caller; signing is a separate phase (Step 18).
            A WARNING is added so the caller is reminded.
        dry_run:
            When ``True``, resolves the source and plans the build without
            creating any directory or launching any subprocess.
        """
        validation = self._validate_inputs(
            kernel_release=kernel_release,
            driver_version=driver_version,
            module_flavor=module_flavor,
            headers_dir=headers_dir,
            output_dir=output_dir,
        )
        if validation is not None:
            return validation

        output_dir = Path(output_dir)
        if workspace_root is not None and not output_dir.is_absolute():
            output_dir = Path(workspace_root) / output_dir
        output_dir = output_dir.resolve(strict=False)
        for dest in (output_dir,):
            bad = check_path_destination_safe(dest, workspace_root=workspace_root)
            if bad:
                return self._error_result(
                    kernel_release=kernel_release, driver_version=driver_version,
                    module_flavor=module_flavor, source_dir=None,
                    code=bad[0].code, message=bad[0].message,
                )
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+~-]*", kernel_release) or not re.fullmatch(r"[0-9][0-9.]*", driver_version):
            return self._error_result(
                kernel_release=kernel_release, driver_version=driver_version,
                module_flavor=module_flavor, source_dir=None,
                code="UNSAFE_BUILD_IDENTIFIER",
                message="Release and driver identifiers must be safe path components.",
            )
        source_dir, source_finding = self._resolve_source(
            driver_version=driver_version,
            dkms_source_dir=dkms_source_dir,
            allow_system_dkms_discovery=allow_system_dkms_discovery,
        )
        if source_dir is None:
            return self._error_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=None,
                code=source_finding.code if source_finding and source_finding.severity == Severity.ERROR else "DKMS_SOURCE_NOT_FOUND",
                message=(
                    source_finding.message
                    if source_finding
                    else (
                        f"No DKMS source found for nvidia {driver_version}. "
                        "Pass dkms_source_dir explicitly or set "
                        "allow_system_dkms_discovery=True."
                    )
                ),
            )

        if (output_dir == source_dir or output_dir in source_dir.parents
                or source_dir in output_dir.parents):
            return self._error_result(
                kernel_release=kernel_release, driver_version=driver_version,
                module_flavor=module_flavor, source_dir=source_dir,
                code="UNSAFE_OUTPUT_OVERLAP",
                message="Staging cannot overlap the vendor source tree.",
            )
        source_version = self._read_dkms_version(source_dir)
        if source_version is not None and source_version != driver_version:
            return self._error_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=source_dir,
                code="DKMS_VERSION_MISMATCH",
                message=(
                    f"DKMS source at {source_dir} reports version "
                    f"{source_version!r} but the pinned driver version is "
                    f"{driver_version!r}."
                ),
            )

        if not (source_dir / "dkms.conf").is_file():
            return self._error_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=source_dir,
                code="DKMS_CONF_MISSING",
                message=f"DKMS source has no dkms.conf: {source_dir}",
            )

        if not any(
            (source_dir / name).is_file()
            for name in ("Makefile", "Kbuild", "makefile")
        ):
            return self._error_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=source_dir,
                code="DKMS_MAKEFILE_MISSING",
                message=(
                    f"DKMS source has no Makefile/Kbuild: {source_dir}. "
                    "External kernel modules require one of these."
                ),
            )

        if dry_run:
            return self._dry_run_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=source_dir,
                output_dir=output_dir,
                headers_dir=headers_dir,
                secure_boot_enabled=secure_boot_enabled,
            )

        findings: list[ValidationFinding] = []

        if module_flavor == ModuleFlavor.OPEN:
            # Already rejected by _validate_inputs, but keep the structural
            # check so a future caller cannot bypass it.
            return self._error_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=source_dir,
                code="OPEN_MODULE_REJECTED",
                message=(
                    "The NVIDIA open GPU kernel modules are not compatible "
                    "with Volta (sm_70). Use the proprietary R580 modules."
                ),
            )

        if secure_boot_enabled:
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="SECUREBOOT_SIGNING_DEFERRED",
                    message=(
                        "Secure Boot is enabled. The staged modules must be "
                        "signed in a separate phase (Step 18) before they "
                        "can load on the target. This build does not sign."
                    ),
                )
            )

        staging_dir = (
            output_dir
            / f"nvidia-{driver_version}-{kernel_release}"
        )
        if staging_dir.is_symlink():
            return self._error_result(
                kernel_release=kernel_release, driver_version=driver_version,
                module_flavor=module_flavor, source_dir=source_dir,
                code="STAGING_SYMLINK_REFUSED",
                message="Refusing symlinked NVIDIA staging directory.",
            )

        # Remove any prior staging to keep the build idempotent.
        if staging_dir.exists():
            try:
                shutil.rmtree(staging_dir)
            except OSError as exc:
                return self._error_result(
                    kernel_release=kernel_release,
                    driver_version=driver_version,
                    module_flavor=module_flavor,
                    source_dir=source_dir,
                    code="STAGING_CLEANUP_FAILED",
                    message=f"Could not remove stale {staging_dir}: {exc}",
                )
        try:
            staging_dir.mkdir(parents=True, exist_ok=False)
        except OSError as exc:
            return self._error_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=source_dir,
                code="STAGING_DIR_CREATE_FAILED",
                message=f"Could not create {staging_dir}: {exc}",
            )

        # Stage a private, writable vendor source copy: make can generate files.
        build_source = staging_dir / "vendor-source"
        try:
            for entry in source_dir.rglob("*"):
                if entry.is_symlink():
                    raise OSError(f"Refusing DKMS source symlink: {entry}")
            shutil.copytree(source_dir, build_source)
            # Never mistake cached .ko files for modules produced by this build.
            for stale_ko in build_source.rglob("*.ko"):
                stale_ko.unlink()
        except OSError as exc:
            return self._error_result(
                kernel_release=kernel_release, driver_version=driver_version,
                module_flavor=module_flavor, source_dir=source_dir,
                code="SOURCE_STAGING_FAILED",
                message=f"Cannot isolate vendor source for build: {exc}",
            )

        # ---- build -----------------------------------------------------
        build_outcome = self._run_build(
            source_dir=build_source,
            headers_dir=headers_dir,
            kernel_release=kernel_release,
        )
        if isinstance(build_outcome, NvidiaBuildResult):
            return build_outcome

        # ---- locate .ko files -----------------------------------------
        built_ko = self._locate_built_modules(build_source)
        if not built_ko:
            return self._error_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=source_dir,
                code="NO_MODULES_BUILT",
                message=(
                    "NVIDIA build completed but no .ko files were produced "
                    f"under {source_dir}. Verify the build output directory "
                    "and the DKMS makefile."
                ),
            )

        # ---- stage and verify ------------------------------------------
        artifacts: dict[str, BuildArtifact] = {}
        for module_name, ko_path in built_ko.items():
            staged_path = staging_dir / f"{module_name}.ko"
            try:
                shutil.copy2(ko_path, staged_path)
            except OSError as exc:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="STAGE_COPY_FAILED",
                        message=(
                            f"Could not copy {ko_path} to {staged_path}: {exc}"
                        ),
                    )
                )
                continue

            vermagic_finding = self._verify_vermagic(
                staged_path, kernel_release
            )
            if vermagic_finding is not None:
                findings.append(vermagic_finding)
                continue

            version_finding = self._verify_module_version(
                staged_path, driver_version
            )
            if version_finding is not None:
                findings.append(version_finding)
                continue

            artifact = self._artifact_from_path(
                staged_path, output_dir, kernel_release,
                ArtifactKind.NVIDIA_MODULE, module_name,
            )
            if artifact is None:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="ARTIFACT_PATH_INVALID",
                        message=(
                            f"Staged module {staged_path.name} cannot be "
                            "represented as a build artifact."
                        ),
                    )
                )
                continue
            artifacts[module_name] = artifact

        # Required modules must be present.
        for required in REQUIRED_MODULES:
            if required not in artifacts:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="REQUIRED_MODULE_MISSING",
                        message=(
                            f"Required module {required!r} was not staged. "
                            "NVIDIA compute requires both nvidia and "
                            "nvidia-uvm to be present and verified."
                        ),
                        context={
                            "required": list(REQUIRED_MODULES),
                            "staged": sorted(artifacts),
                        },
                    )
                )

        logger.info(
            "nvidia.build complete driver=%s kernel_release=%s modules=%s "
            "errors=%d",
            driver_version,
            kernel_release,
            sorted(artifacts),
            sum(
                1 for f in findings
                if f.severity in (Severity.ERROR, Severity.CRITICAL)
            ),
        )

        return NvidiaBuildResult(
            kernel_release=kernel_release,
            driver_version=driver_version,
            module_flavor=module_flavor,
            source_dir=source_dir,
            module_artifacts=artifacts,
            findings=tuple(findings),
            dry_run=False,
        )

    # ---- internals -------------------------------------------------------

    def _validate_inputs(
        self,
        *,
        kernel_release: str,
        driver_version: str,
        module_flavor: ModuleFlavor,
        headers_dir: Path,
        output_dir: Path,
    ) -> NvidiaBuildResult | None:
        if not kernel_release or not kernel_release.strip():
            return self._error_result(
                kernel_release=None,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=None,
                code="KERNEL_RELEASE_MISSING",
                message="kernel_release must be a non-empty string.",
            )
        if not driver_version or not driver_version.strip():
            return self._error_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=None,
                code="DRIVER_VERSION_MISSING",
                message="driver_version must be a non-empty string.",
            )
        if not isinstance(module_flavor, ModuleFlavor):
            return self._error_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=ModuleFlavor.PROPRIETARY,
                source_dir=None,
                code="MODULE_FLAVOR_INVALID",
                message=(
                    f"module_flavor must be a ModuleFlavor, got "
                    f"{type(module_flavor).__name__}."
                ),
            )
        if module_flavor == ModuleFlavor.OPEN:
            return self._error_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=None,
                code="OPEN_MODULE_REJECTED",
                message=(
                    "The NVIDIA open GPU kernel modules do not support Volta "
                    "(sm_70). Tesla V100 requires the proprietary R580 "
                    "modules."
                ),
            )
        headers_dir = Path(headers_dir)
        if not (headers_dir / "Makefile").is_file():
            return self._error_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=None,
                code="HEADERS_MAKEFILE_MISSING",
                message=(
                    f"headers_dir has no Makefile: {headers_dir}. External "
                    "module builds require the matching headers tree."
                ),
            )
        if not (headers_dir / "include" / "generated").is_dir():
            return self._error_result(
                kernel_release=kernel_release,
                driver_version=driver_version,
                module_flavor=module_flavor,
                source_dir=None,
                code="HEADERS_GENERATED_MISSING",
                message=(
                    f"headers_dir has no include/generated: {headers_dir}. "
                    "The headers must be a fully prepared tree for the exact "
                    "target kernel release."
                ),
            )
        return None

    def _resolve_source(
        self,
        *,
        driver_version: str,
        dkms_source_dir: Path | None,
        allow_system_dkms_discovery: bool,
    ) -> tuple[Path | None, ValidationFinding | None]:
        if dkms_source_dir is not None:
            path = Path(dkms_source_dir)
            if not path.is_dir():
                return None, ValidationFinding(
                    severity=Severity.ERROR,
                    code="DKMS_SOURCE_DIR_MISSING",
                    message=(
                        f"Provided dkms_source_dir does not exist or is not a "
                        f"directory: {path}"
                    ),
                )
            return path.resolve(), None

        if not allow_system_dkms_discovery:
            return None, ValidationFinding(
                severity=Severity.INFO,
                code="SYSTEM_DKMS_DISCOVERY_DISABLED",
                message=(
                    "System DKMS discovery is disabled. Pass dkms_source_dir "
                    "or set allow_system_dkms_discovery=True to use the "
                    "system DKMS tree."
                ),
            )

        for template in _DEFAULT_DKMS_SOURCE_ROOTS:
            candidate = Path(template.format(version=driver_version))
            if candidate.is_dir():
                return candidate.resolve(), None

        return None, ValidationFinding(
            severity=Severity.ERROR,
            code="DKMS_SOURCE_NOT_FOUND",
            message=(
                f"No DKMS source found for nvidia {driver_version}. "
                f"Searched: {[t.format(version=driver_version) for t in _DEFAULT_DKMS_SOURCE_ROOTS]}."
            ),
        )

    def _read_dkms_version(self, source_dir: Path) -> str | None:
        dkms_conf = source_dir / "dkms.conf"
        if not dkms_conf.is_file():
            return None
        try:
            text = dkms_conf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("PACKAGE_VERSION="):
                value = line.split("=", 1)[1].strip()
                return value.strip('"').strip("'") or None
        return None

    def _run_build(
        self,
        *,
        source_dir: Path,
        headers_dir: Path,
        kernel_release: str,
    ) -> NvidiaBuildResult | str:
        # The kernel's external-module build system uses these variables.
        # Some DKMS packages set them via dkms.conf; setting them explicitly
        # here overrides any stale values so the build cannot accidentally
        # target a different kernel.
        spec = CommandSpec(
            argv=(
                "make",
                "modules",
                "-j4",
            ),
            cwd=source_dir,
            description=f"NVIDIA module build for {kernel_release}",
            timeout_seconds=_DKMS_BUILD_TIMEOUT_SECONDS,
            env_overrides={
                "KERNELRELEASE": kernel_release,
                "KERNEL_DIR": str(headers_dir.resolve()),
                "KERNEL_SOURCE": str(headers_dir.resolve()),
                "SYSSRC": str(headers_dir.resolve()),
                "SYSOUT": str(headers_dir.resolve()),
            },
        )
        try:
            result = self._runner.run(spec)
        except RunnerTimeout as exc:
            return self._error_result(
                kernel_release=kernel_release,
                driver_version="",
                module_flavor=ModuleFlavor.PROPRIETARY,
                source_dir=source_dir,
                code="NVIDIA_BUILD_TIMEOUT",
                message=f"NVIDIA build timed out: {exc}",
            )
        except RunnerError as exc:
            return self._error_result(
                kernel_release=kernel_release,
                driver_version="",
                module_flavor=ModuleFlavor.PROPRIETARY,
                source_dir=source_dir,
                code="NVIDIA_BUILD_LAUNCH_FAILED",
                message=f"NVIDIA build could not launch: {exc}",
            )
        if not result.succeeded:
            return self._error_result(
                kernel_release=kernel_release,
                driver_version="",
                module_flavor=ModuleFlavor.PROPRIETARY,
                source_dir=source_dir,
                code="NVIDIA_BUILD_FAILED",
                message=(
                    f"NVIDIA build exited {result.command.returncode}. This is "
                    "incompatibility evidence for the target kernel; do not "
                    "patch vendor source without a separately reviewed change."
                ),
            )
        return "ok"

    def _locate_built_modules(self, source_dir: Path) -> dict[str, Path]:
        """Find ``.ko`` files by exact module name under ``source_dir``."""
        found: dict[str, Path] = {}
        for ko in source_dir.rglob("*.ko"):
            name = ko.stem  # strips ".ko"
            # Only accept modules we know how to stage.
            if name in REQUIRED_MODULES or name in OPTIONAL_MODULES:
                if name not in found:
                    found[name] = ko
        return found

    def _verify_vermagic(
        self, module_path: Path, expected_release: str
    ) -> ValidationFinding | None:
        spec = CommandSpec(
            argv=("modinfo", "-F", "vermagic", str(module_path)),
            cwd=module_path.parent,
            description=f"modinfo vermagic for {module_path.name}",
            timeout_seconds=_VERMAGIC_TIMEOUT_SECONDS,
        )
        try:
            result = self._runner.run(spec)
        except (RunnerError, RunnerTimeout) as exc:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="VERMAGIC_UNAVAILABLE",
                message=(
                    f"Could not query vermagic of {module_path.name}: {exc}"
                ),
            )
        if not result.succeeded:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="VERMAGIC_QUERY_FAILED",
                message=(
                    f"modinfo vermagic exited {result.command.returncode} for "
                    f"{module_path.name}"
                ),
            )
        text = (result.stdout or b"").decode("utf-8", errors="replace").strip()
        # Vermagic format: "5.15.0-91-generic SMP mod_unload modversions"
        # The first token is the exact kernel release.
        first = text.split()[0] if text else ""
        if first != expected_release:
            return ValidationFinding(
                severity=Severity.CRITICAL,
                code="VERMAGIC_MISMATCH",
                message=(
                    f"{module_path.name} vermagic release is {first!r}, "
                    f"expected {expected_release!r}. The module will not load "
                    "on the target kernel."
                ),
                context={
                    "module": module_path.name,
                    "expected": expected_release,
                    "actual": first,
                    "full_vermagic": text,
                },
            )
        return None

    def _verify_module_version(
        self, module_path: Path, expected_version: str
    ) -> ValidationFinding | None:
        spec = CommandSpec(
            argv=("modinfo", "-F", "version", str(module_path)),
            cwd=module_path.parent,
            description=f"modinfo version for {module_path.name}",
            timeout_seconds=_MODINFO_TIMEOUT_SECONDS,
        )
        try:
            result = self._runner.run(spec)
        except (RunnerError, RunnerTimeout) as exc:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="MODULE_VERSION_UNAVAILABLE",
                message=(
                    f"Could not query version of {module_path.name}: {exc}"
                ),
            )
        if not result.succeeded:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="MODULE_VERSION_QUERY_FAILED",
                message=(
                    f"modinfo version exited {result.command.returncode} for "
                    f"{module_path.name}"
                ),
            )
        actual = (result.stdout or b"").decode("utf-8", errors="replace").strip()
        if actual != expected_version:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="MODULE_VERSION_MISMATCH",
                message=(
                    f"{module_path.name} version is {actual!r}, expected "
                    f"{expected_version!r}."
                ),
                context={
                    "module": module_path.name,
                    "expected": expected_version,
                    "actual": actual,
                },
            )
        return None

    @staticmethod
    def _sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _artifact_from_path(
        self,
        path: Path,
        output_dir: Path,
        kernel_release: str,
        kind: ArtifactKind,
        module_name: str,
    ) -> BuildArtifact | None:
        try:
            rel = path.resolve().relative_to(output_dir.resolve())
        except (ValueError, OSError):
            return None
        if rel.is_absolute() or ".." in rel.parts:
            return None
        try:
            sha = self._sha256_file(path)
            size = path.stat().st_size
        except OSError:
            return None
        return BuildArtifact(
            kind=kind,
            path=str(rel),
            sha256=sha,
            size_bytes=size,
            kernel_release=kernel_release,
        )

    def _dry_run_result(
        self,
        *,
        kernel_release: str,
        driver_version: str,
        module_flavor: ModuleFlavor,
        source_dir: Path,
        output_dir: Path,
        headers_dir: Path,
        secure_boot_enabled: bool,
    ) -> NvidiaBuildResult:
        findings = [
            ValidationFinding(
                severity=Severity.INFO,
                code="NVIDIA_BUILD_DRY_RUN",
                message=(
                    f"Planned: build {driver_version} modules for "
                    f"{kernel_release} from {source_dir} into "
                    f"{output_dir}/nvidia-{driver_version}-{kernel_release}. "
                    "No files were written and no subprocess was launched."
                ),
                context={
                    "kernel_release": kernel_release,
                    "driver_version": driver_version,
                    "module_flavor": module_flavor.value,
                    "source_dir": str(source_dir),
                    "headers_dir": str(headers_dir),
                    "output_dir": str(output_dir),
                    "secure_boot_enabled": secure_boot_enabled,
                },
            ),
        ]
        if secure_boot_enabled:
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="SECUREBOOT_SIGNING_DEFERRED",
                    message=(
                        "Secure Boot is enabled. Staged modules will need "
                        "signing in a separate phase (Step 18)."
                    ),
                )
            )
        return NvidiaBuildResult(
            kernel_release=kernel_release,
            driver_version=driver_version,
            module_flavor=module_flavor,
            source_dir=source_dir,
            module_artifacts={},
            findings=tuple(findings),
            dry_run=True,
        )

    @staticmethod
    def _error_result(
        *,
        kernel_release: str | None,
        driver_version: str,
        module_flavor: ModuleFlavor,
        source_dir: Path | None,
        code: str,
        message: str,
    ) -> NvidiaBuildResult:
        return NvidiaBuildResult(
            kernel_release=kernel_release,
            driver_version=driver_version,
            module_flavor=module_flavor,
            source_dir=source_dir,
            module_artifacts={},
            findings=(
                ValidationFinding(
                    severity=Severity.ERROR, code=code, message=message
                ),
            ),
            dry_run=False,
        )
