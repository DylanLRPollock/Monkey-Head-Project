"""Offline verification for HueyOS kernel release artifacts.

Checks a release directory against the expected metadata without touching
the host or requiring GPU/network access. Three categories of check are
distinguished:

* **Static** (this module, offline): package names via ``dpkg-deb``, kernel
  release matching in package names and module vermagic, NVIDIA driver
  version matching, module dependency closure, initramfs contents, signature
  fingerprints via ``modinfo -F sig_key``, SHA-256 for a manifest, and
  source-lock status. These run on any machine with the release tree and
  the read-only tools ``dpkg-deb``, ``modinfo``, ``lsinitramfs``.
* **Host** (deferred to Step 29's runbook): the target kernel boots, the
  GRUB entry exists and can be rolled back, Secure Boot trusts the signed
  modules via MOK, AMDGPU display works on the RX 570.
* **Runtime** (deferred to Step 29's runbook): the V100 is enumerated by
  NVML, CUDA smoke test passes, Ollama and ComfyUI select the V100,
  Steam/Proton Vulkan wrapper still works, thermal behavior is controlled.

A build is ``boot_ready`` only when all static checks pass. When
``boot_ready`` is True, ``host_checks_required`` lists the host and runtime
checks that remain for the human-operated qualification; when False, static
failures must be fixed first and re-verified before any host check is
meaningful.

Artifact paths in ``VerificationContext.manifest_artifacts`` are resolved
relative to ``VerificationContext.release_dir``. Callers must construct
those ``BuildArtifact`` objects with paths relative to ``release_dir``.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from huey.kernel_build.models import (
    BuildArtifact,
    Severity,
    ValidationFinding,
)
from huey.kernel_build.policy import SecureBootState
from huey.kernel_build.runner import (
    CommandSpec,
    RunnerError,
    RunnerProtocol,
    RunnerTimeout,
)

logger = logging.getLogger(__name__)

__all__ = [
    "HOST_CHECKS",
    "ReleaseVerifier",
    "VerificationContext",
    "VerificationResult",
]

_DPKG_DEB_TIMEOUT_SECONDS: float = 30.0
_MODINFO_TIMEOUT_SECONDS: float = 30.0
_LSINITRAMFS_TIMEOUT_SECONDS: float = 60.0

_KO_SUFFIXES: tuple[str, ...] = (
    ".ko.zst",
    ".ko.xz",
    ".ko.gz",
    ".ko.bz2",
    ".ko",
)

_FORBIDDEN_INITRAMFS_MODULES: tuple[str, ...] = ("nouveau",)

#: Host and runtime checks that must be performed on the target (Step 29's
#: runbook). Returned in ``VerificationResult.host_checks_required`` when
#: ``boot_ready=True`` so the operator sees exactly what remains.
HOST_CHECKS: tuple[str, ...] = (
    "boot_and_storage",       # custom kernel boots, root fs mounted
    "grub_entry",             # bootloader entry present, rollback possible
    "secure_boot_trust",      # signed modules load under Secure Boot / MOK
    "amdgpu_display",         # RX 570 display path intact
    "nvidia_module_load",     # proprietary nvidia / nvidia-uvm loaded
    "nvidia_nvml",            # nvidia-smi reports the V100 by PCI/UUID
    "cuda_smoke",             # small CUDA workload runs on the V100
    "ollama",                 # Ollama selects the V100
    "comfyui",                # ComfyUI selects the V100
    "steam_proton_vulkan",    # opt-in Vulkan wrapper still works
    "thermal",                # idle and load temperatures within limits
)


# ---------------------------------------------------------------------------
# Context and result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class VerificationContext:
    """Inputs for a verification run.

    ``release_dir`` is the root for all relative paths, including the
    ``manifest_artifacts[*].path`` entries. ``expected_packages`` are
    Debian package names (e.g. ``"linux-image-7.2.15-huey1"``); the
    verifier queries ``dpkg-deb --field <deb> Package`` to locate them.
    """

    release_dir: Path
    kernel_release: str
    driver_version: str
    expected_packages: tuple[str, ...] = ()
    required_modules: tuple[str, ...] = ()
    module_tree_dir: Path | None = None
    initramfs_path: Path | None = None
    manifest_artifacts: tuple[BuildArtifact, ...] = ()
    require_signed_modules: bool = False
    expected_cert_fingerprint: str | None = None
    lockfile_path: Path | None = None
    secure_boot_state: SecureBootState = SecureBootState.UNKNOWN

    def __post_init__(self) -> None:
        object.__setattr__(self, "release_dir", Path(self.release_dir))
        if self.module_tree_dir is not None:
            object.__setattr__(self, "module_tree_dir", Path(self.module_tree_dir))
        if self.initramfs_path is not None:
            object.__setattr__(self, "initramfs_path", Path(self.initramfs_path))
        if self.lockfile_path is not None:
            object.__setattr__(self, "lockfile_path", Path(self.lockfile_path))
        for name in (
            "expected_packages",
            "required_modules",
            "manifest_artifacts",
        ):
            value = getattr(self, name)
            if isinstance(value, list):
                object.__setattr__(self, name, tuple(value))


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Outcome of a verification run."""

    findings: tuple[ValidationFinding, ...]
    boot_ready: bool
    static_checks_passed: bool
    host_checks_required: tuple[str, ...]
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
            "findings": [f.to_dict() for f in self.findings],
            "boot_ready": self.boot_ready,
            "static_checks_passed": self.static_checks_passed,
            "host_checks_required": list(self.host_checks_required),
            "dry_run": self.dry_run,
        }


# ---------------------------------------------------------------------------
# ReleaseVerifier
# ---------------------------------------------------------------------------


class ReleaseVerifier:
    """Verify a HueyOS kernel release directory offline."""

    def __init__(self, runner: RunnerProtocol) -> None:
        self._runner = runner

    # ---- public API ------------------------------------------------------

    def verify_release(
        self,
        ctx: VerificationContext,
        *,
        dry_run: bool = False,
    ) -> VerificationResult:
        """Run all static checks against ``ctx`` and return a consolidated result.

        ``dry_run=True`` skips all subprocess checks (``dpkg-deb``,
        ``modinfo``, ``lsinitramfs``); only filesystem checks (existence,
        SHA-256, lockfile) are performed. ``boot_ready`` is False because
        the full verification did not run; findings explain what was
        skipped and why.
        """
        if not ctx.release_dir.is_dir():
            return self._early_error(
                code="RELEASE_DIR_MISSING",
                message=f"release_dir is not a directory: {ctx.release_dir}",
                dry_run=dry_run,
            )

        findings: list[ValidationFinding] = []

        if dry_run:
            findings.append(
                ValidationFinding(
                    severity=Severity.INFO,
                    code="VERIFY_DRY_RUN",
                    message=(
                        "dry_run=True: subprocess checks (dpkg-deb, modinfo, "
                        "lsinitramfs) were skipped. Only filesystem checks "
                        "(existence, SHA-256, lockfile) were performed. "
                        "boot_ready cannot be confirmed in dry-run mode."
                    ),
                )
            )
            findings.extend(self._verify_hashes(ctx))
            findings.extend(self._verify_lockfile(ctx))
            blocking = [
                f for f in findings
                if f.severity in (Severity.ERROR, Severity.CRITICAL)
            ]
            return VerificationResult(
                findings=tuple(findings),
                boot_ready=False,  # dry_run cannot confirm readiness
                static_checks_passed=not blocking,
                host_checks_required=(),
                dry_run=True,
            )

        # 1. Package metadata (dpkg-deb Package field)
        if not ctx.expected_packages:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="NO_EXPECTED_PACKAGES",
                    message="expected_packages is empty; package checks skipped.",
                )
            )
        else:
            findings.extend(self._verify_packages(ctx))

        # 2. Module metadata (vermagic for all, version for nvidia)
        if not ctx.required_modules:
            findings.append(ValidationFinding(
                severity=Severity.ERROR, code="REQUIRED_MODULES_MISSING",
                message="At least one required module must be verified.",
            ))
        findings.extend(self._verify_module_metadata(ctx))

        # 3. Dependency closure
        if ctx.module_tree_dir is None:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="DEPENDENCY_CLOSURE_SKIPPED",
                    message=(
                        "module_tree_dir not provided; module dependency "
                        "closure was not verified."
                    ),
                )
            )
        else:
            findings.extend(self._verify_module_dependencies(ctx))

        # 4. Initramfs contents
        if ctx.initramfs_path is None:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="INITRAMFS_VERIFICATION_SKIPPED",
                    message="initramfs_path not provided; initramfs checks skipped.",
                )
            )
        else:
            findings.extend(self._verify_initramfs(ctx))

        # 5. Secure Boot compatibility
        findings.extend(self._verify_secure_boot_compat(ctx))

        # 6. Signing
        if ctx.require_signed_modules or ctx.secure_boot_state == SecureBootState.ENABLED:
            findings.extend(self._verify_signing(ctx))

        # 7. Manifest hashes
        findings.extend(self._verify_hashes(ctx))

        # 8. Lockfile
        findings.extend(self._verify_lockfile(ctx))

        blocking = [
            f for f in findings
            if f.severity in (Severity.ERROR, Severity.CRITICAL)
        ]
        static_ok = not blocking
        boot_ready = static_ok
        host_checks = HOST_CHECKS if boot_ready else ()

        logger.info(
            "verify.complete release_dir=%s boot_ready=%s blocking=%d total=%d",
            ctx.release_dir,
            boot_ready,
            len(blocking),
            len(findings),
        )

        return VerificationResult(
            findings=tuple(findings),
            boot_ready=boot_ready,
            static_checks_passed=static_ok,
            host_checks_required=host_checks,
            dry_run=False,
        )

    # ---- package verification -------------------------------------------

    def _verify_packages(
        self, ctx: VerificationContext
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        debs = sorted(ctx.release_dir.rglob("*.deb"))
        if not debs:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="NO_DEBS_IN_RELEASE",
                    message=f"No .deb files found under {ctx.release_dir}.",
                )
            )
            return findings

        package_to_deb: dict[str, Path] = {}
        for deb in debs:
            pkg = self._query_deb_field(deb, "Package")
            if pkg is None:
                findings.append(
                    ValidationFinding(
                        severity=Severity.WARNING,
                        code="PACKAGE_FIELD_UNAVAILABLE",
                        message=f"Could not query Package field of {deb.name}.",
                    )
                )
                continue
            package_to_deb.setdefault(pkg, deb)

        for expected in ctx.expected_packages:
            if expected not in package_to_deb:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="EXPECTED_PACKAGE_MISSING",
                        message=(
                            f"No .deb declares Package: {expected!r}. "
                            f"Found: {sorted(package_to_deb)}"
                        ),
                        context={
                            "expected": expected,
                            "found": sorted(package_to_deb),
                        },
                    )
                )
        return findings

    # ---- module metadata -------------------------------------------------

    def _verify_module_metadata(
        self, ctx: VerificationContext
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        kos = self._find_modules(ctx.release_dir)
        if not kos:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="NO_MODULES_FOUND",
                    message="No .ko/.ko.* files found in release directory.",
                )
            )
            return findings

        for ko in kos:
            vermagic = self._query_modinfo(ko, "vermagic")
            if vermagic is None:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="VERMAGIC_UNAVAILABLE",
                        message=f"Could not query vermagic of {ko.name}.",
                    )
                )
            else:
                first = vermagic.split()[0] if vermagic else ""
                if first != ctx.kernel_release:
                    findings.append(
                        ValidationFinding(
                            severity=Severity.CRITICAL,
                            code="VERMAGIC_MISMATCH",
                            message=(
                                f"{ko.name} vermagic release is {first!r}, "
                                f"expected {ctx.kernel_release!r}."
                            ),
                            context={
                                "module": ko.name,
                                "expected": ctx.kernel_release,
                                "actual": first,
                            },
                        )
                    )

            if self._is_nvidia_module(ko.name):
                version = self._query_modinfo(ko, "version")
                if version is not None and version != ctx.driver_version:
                    findings.append(
                        ValidationFinding(
                            severity=Severity.ERROR,
                            code="MODULE_VERSION_MISMATCH",
                            message=(
                                f"{ko.name} version is {version!r}, expected "
                                f"{ctx.driver_version!r}."
                            ),
                            context={
                                "module": ko.name,
                                "expected": ctx.driver_version,
                                "actual": version,
                            },
                        )
                    )
        return findings

    # ---- dependency closure ---------------------------------------------

    def _verify_module_dependencies(
        self, ctx: VerificationContext
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        kos = self._find_modules(ctx.release_dir)

        available: set[str] = set()
        modules_dep = Path(ctx.module_tree_dir) / "modules.dep"
        if modules_dep.is_file():
            try:
                for line in modules_dep.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines():
                    if ":" in line:
                        path = line.split(":", 1)[0].strip()
                        available.add(self._module_basename(Path(path).name))
            except OSError as exc:
                findings.append(
                    ValidationFinding(
                        severity=Severity.WARNING,
                        code="MODULES_DEP_UNREADABLE",
                        message=f"Could not read {modules_dep}: {exc}",
                    )
                )
        else:
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="MODULES_DEP_MISSING",
                    message=(
                        f"{modules_dep} not found; dependency closure will "
                        "only consider staged modules."
                    ),
                )
            )

        staged_names = {self._module_basename(ko.name) for ko in kos}
        available |= staged_names

        for ko in kos:
            depends = self._query_modinfo(ko, "depends")
            if depends is None:
                findings.append(
                    ValidationFinding(
                        severity=Severity.WARNING,
                        code="DEPENDS_UNAVAILABLE",
                        message=f"Could not query depends of {ko.name}.",
                    )
                )
                continue
            if not depends:
                continue
            for dep in depends.split(","):
                dep = dep.strip()
                if not dep:
                    continue
                if dep not in available:
                    findings.append(
                        ValidationFinding(
                            severity=Severity.ERROR,
                            code="MODULE_DEPENDENCY_MISSING",
                            message=(
                                f"{ko.name} depends on {dep!r}, which is not "
                                "in modules.dep or the staged modules."
                            ),
                            context={"module": ko.name, "missing": dep},
                        )
                    )
        return findings

    # ---- initramfs -------------------------------------------------------

    def _verify_initramfs(
        self, ctx: VerificationContext
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        archive = Path(ctx.initramfs_path)
        if not archive.is_file():
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="INITRAMFS_ARCHIVE_MISSING",
                    message=f"initramfs archive not found: {archive}",
                )
            )
            return findings

        listing = self._run_lsinitramfs(archive)
        if listing is None:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="LSINITRAMFS_FAILED",
                    message=(
                        f"Could not obtain listing for {archive.name}; "
                        "initramfs contents not verified."
                    ),
                )
            )
            return findings

        prefix = f"lib/modules/{ctx.kernel_release}/"
        if not any(entry.startswith(prefix) for entry in listing):
            findings.append(
                ValidationFinding(
                    severity=Severity.CRITICAL,
                    code="INITRAMFS_WRONG_RELEASE",
                    message=(
                        f"None of the archive entries begin with {prefix!r}; "
                        "the initramfs targets a different kernel release."
                    ),
                    context={"kernel_release": ctx.kernel_release},
                )
            )

        present = {self._module_basename(Path(e).name) for e in listing}
        for mod in ctx.required_modules:
            if mod not in present:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="INITRAMFS_REQUIRED_MODULE_MISSING",
                        message=(
                            f"Required module {mod!r} not present in "
                            f"{archive.name}."
                        ),
                        context={"module": mod},
                    )
                )

        for forbidden in _FORBIDDEN_INITRAMFS_MODULES:
            if forbidden in present:
                findings.append(
                    ValidationFinding(
                        severity=Severity.CRITICAL,
                        code="INITRAMFS_FORBIDDEN_MODULE_PRESENT",
                        message=(
                            f"Forbidden module {forbidden!r} appears in "
                            f"{archive.name}. The V100 must not be claimed "
                            "by Nouveau."
                        ),
                    )
                )
        return findings

    # ---- Secure Boot compatibility --------------------------------------

    def _verify_secure_boot_compat(
        self, ctx: VerificationContext
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        if ctx.secure_boot_state == SecureBootState.ENABLED and not ctx.require_signed_modules:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="SECUREBOOT_SIGNING_POLICY_MISMATCH",
                    message=(
                        "Secure Boot is enabled but require_signed_modules="
                        "False. The release would not load on the target."
                    ),
                )
            )
        elif ctx.secure_boot_state == SecureBootState.UNKNOWN:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="SECUREBOOT_STATE_UNKNOWN",
                    message=(
                        "Secure Boot state is unknown. boot_ready is "
                        "provisional; confirm with 'mokutil --sb-state' on "
                        "the target before promoting the release."
                    ),
                )
            )
        return findings

    # ---- signing ---------------------------------------------------------

    def _verify_signing(
        self, ctx: VerificationContext
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        if not ctx.expected_cert_fingerprint:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="CERT_FINGERPRINT_NOT_PROVIDED",
                    message=(
                        "Signing is required but expected_cert_fingerprint "
                        "was not provided; cannot verify signer identity."
                    ),
                )
            )
            return findings

        kos = self._find_modules(ctx.release_dir)
        by_name = {self._module_basename(ko.name): ko for ko in kos}

        for mod in ctx.required_modules:
            ko = by_name.get(mod)
            if ko is None:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="REQUIRED_MODULE_FILE_MISSING",
                        message=(
                            f"Required module {mod!r} not found among staged "
                            f"modules: {sorted(by_name)}."
                        ),
                    )
                )
                continue
            sig_key = self._query_modinfo(ko, "sig_key")
            if sig_key is None:
                findings.append(
                    ValidationFinding(
                        severity=Severity.CRITICAL,
                        code="REQUIRED_MODULE_UNSIGNED",
                        message=(
                            f"Required module {mod!r} is not signed "
                            "(no sig_key in modinfo)."
                        ),
                    )
                )
                continue
            if sig_key.upper() != ctx.expected_cert_fingerprint.upper():
                findings.append(
                    ValidationFinding(
                        severity=Severity.CRITICAL,
                        code="REQUIRED_MODULE_SIGNED_BY_WRONG_KEY",
                        message=(
                            f"Required module {mod!r} is signed by a key "
                            f"with fingerprint {sig_key}, not the expected "
                            f"{ctx.expected_cert_fingerprint}."
                        ),
                        context={
                            "module": mod,
                            "expected": ctx.expected_cert_fingerprint,
                            "actual": sig_key,
                        },
                    )
                )
        return findings

    # ---- hash verification ----------------------------------------------

    def _verify_hashes(
        self, ctx: VerificationContext
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        if not ctx.manifest_artifacts:
            findings.append(ValidationFinding(
                severity=Severity.ERROR, code="MANIFEST_ARTIFACTS_MISSING",
                message="No hashes were provided; artifact verification is incomplete.",
            ))
        for art in ctx.manifest_artifacts:
            full = ctx.release_dir / art.path
            if full.is_symlink() or not full.resolve().is_relative_to(ctx.release_dir.resolve()):
                findings.append(ValidationFinding(
                    severity=Severity.ERROR, code="ARTIFACT_PATH_UNSAFE",
                    message=f"Artifact path escapes release directory: {art.path}",
                ))
                continue
            if not full.is_file():
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="ARTIFACT_FILE_MISSING",
                        message=(
                            f"Artifact {art.path} not found at {full}."
                        ),
                        context={"path": str(art.path)},
                    )
                )
                continue
            try:
                actual = self._sha256_file(full)
            except OSError as exc:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="ARTIFACT_HASH_FAILED",
                        message=f"Could not hash {full}: {exc}",
                    )
                )
                continue
            if actual != art.sha256:
                findings.append(
                    ValidationFinding(
                        severity=Severity.CRITICAL,
                        code="ARTIFACT_SHA256_MISMATCH",
                        message=(
                            f"{art.path}: SHA-256 {actual} != expected "
                            f"{art.sha256}."
                        ),
                        context={
                            "path": str(art.path),
                            "expected": art.sha256,
                            "actual": actual,
                        },
                    )
                )
        return findings

    # ---- lockfile --------------------------------------------------------

    def _verify_lockfile(
        self, ctx: VerificationContext
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        if ctx.lockfile_path is None:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="LOCKFILE_NOT_PROVIDED",
                    message=(
                        "lockfile_path not provided; source pin status was "
                        "not verified."
                    ),
                )
            )
            return findings
        try:
            from huey.kernel_build.source_manager import SourceLock
            lock = SourceLock.load_from_path(Path(ctx.lockfile_path))
        except Exception as exc:  # noqa: BLE001 - any load failure is a finding
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="LOCKFILE_INVALID",
                    message=(
                        f"Could not load {ctx.lockfile_path}: {exc}"
                    ),
                )
            )
            return findings
        if lock.status != "pinned" or lock.checksum_sha256 == "0" * 64:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="LOCKFILE_UNRESOLVED",
                    message=(
                        f"Source lock status is {lock.status!r}; release "
                        "cannot be promoted until the source is pinned."
                    ),
                    context={"status": lock.status},
                )
            )
        return findings

    # ---- helpers ---------------------------------------------------------

    def _query_deb_field(self, deb_path: Path, field_name: str) -> str | None:
        spec = CommandSpec(
            argv=("dpkg-deb", "--field", str(deb_path), field_name),
            cwd=deb_path.parent,
            description=f"dpkg-deb {field_name} {deb_path.name}",
            timeout_seconds=_DPKG_DEB_TIMEOUT_SECONDS,
        )
        try:
            result = self._runner.run(spec)
        except (RunnerError, RunnerTimeout):
            return None
        if not result.succeeded or not result.stdout:
            return None
        text = result.stdout.decode("utf-8", errors="replace")
        prefix = f"{field_name}:"
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(prefix):
                value = stripped[len(prefix):].strip()
                return value or None
        # `dpkg-deb --field package.deb Package` normally prints only the
        # value, not `Package: value` (which fake runners sometimes emit).
        bare = text.strip()
        return bare if bare and "\n" not in bare and ":" not in bare else None

    def _query_modinfo(self, ko_path: Path, field_name: str) -> str | None:
        spec = CommandSpec(
            argv=("modinfo", "-F", field_name, str(ko_path)),
            cwd=ko_path.parent,
            description=f"modinfo -F {field_name} {ko_path.name}",
            timeout_seconds=_MODINFO_TIMEOUT_SECONDS,
        )
        try:
            result = self._runner.run(spec)
        except (RunnerError, RunnerTimeout):
            return None
        if not result.succeeded:
            return None
        text = (result.stdout or b"").decode("utf-8", errors="replace").strip()
        return text or None

    def _run_lsinitramfs(self, archive_path: Path) -> tuple[str, ...] | None:
        spec = CommandSpec(
            argv=("lsinitramfs", str(archive_path)),
            cwd=archive_path.parent,
            description=f"lsinitramfs {archive_path.name}",
            timeout_seconds=_LSINITRAMFS_TIMEOUT_SECONDS,
        )
        try:
            result = self._runner.run(spec)
        except (RunnerError, RunnerTimeout):
            return None
        if not result.succeeded:
            return None
        text = (result.stdout or b"").decode("utf-8", errors="replace")
        lines = tuple(line.strip() for line in text.splitlines() if line.strip())
        return lines

    @staticmethod
    def _find_modules(root: Path) -> list[Path]:
        result: set[Path] = set()
        for suffix in _KO_SUFFIXES:
            result.update(root.rglob(f"*{suffix}"))
        return sorted(result)

    @staticmethod
    def _module_basename(filename: str) -> str:
        for suffix in _KO_SUFFIXES:
            if filename.endswith(suffix):
                return filename[: -len(suffix)]
        return filename

    @staticmethod
    def _is_nvidia_module(filename: str) -> bool:
        name = filename.rsplit("/", 1)[-1]
        return name.startswith("nvidia")

    @staticmethod
    def _sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _early_error(
        *, code: str, message: str, dry_run: bool
    ) -> VerificationResult:
        return VerificationResult(
            findings=(
                ValidationFinding(
                    severity=Severity.ERROR, code=code, message=message
                ),
            ),
            boot_ready=False,
            static_checks_passed=False,
            host_checks_required=(),
            dry_run=dry_run,
        )
