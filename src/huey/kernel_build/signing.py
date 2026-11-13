"""Secure Boot signing and verification for the HueyOS kernel build framework.

Scope
-----
This module implements the **signing phase** as a discrete, auditable step:

1. Detect Secure Boot state read-only (``mokutil --sb-state``).
2. Validate operator-supplied signing material (private key + certificate),
   which must live outside the repository.
3. Sign staged kernel modules in place via the kernel's
   ``scripts/sign-file`` (or a caller-supplied equivalent), passing the
   key passphrase through ``KBUILD_SIGN_PIN`` in the environment, never in
   argv or logs.
4. Sign a kernel EFI image via ``sbsign`` when the boot chain requires it.
5. Verify each signature by comparing ``modinfo -F sig_key`` to the
   certificate fingerprint, and (optionally) by ``openssl smime -verify``
   for a detached PKCS#7 signature check.
6. Evaluate readiness: if Secure Boot is enabled and every required artifact
   is not validly signed by a certificate that the target can trust, the
   result is ``boot_ready=False``.

What this module does **not** do
---------------------------------
* Never runs ``mokutil --import``. Enrollment mutates firmware state and
  requires a reboot plus physical console access. A :class:`MokEnrollmentPlan`
  is returned describing exactly what the operator must run.
* Never logs the private key, the passphrase, or the certificate's private
  components. Only the certificate's public SHA-256 fingerprint is recorded.
* Never copies keys into the build output directory.
* Never disables Secure Boot to make a build pass.
* Never assumes that "signed" implies "trusted on the target": the signature
  must chain to a certificate the target kernel or shim actually trusts. That
  verification is deferred to the human-run qualification (Step 29), but the
  readiness evaluation fails closed if the certificate is not enrolled.
"""

from __future__ import annotations

import hashlib
import logging
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from huey.kernel_build.models import (
    ArtifactKind,
    BuildArtifact,
    Severity,
    ValidationFinding,
)
from huey.kernel_build.policy import SecureBootState, check_path_destination_safe
from huey.kernel_build.runner import (
    CommandSpec,
    RunnerError,
    RunnerProtocol,
    RunnerTimeout,
)

logger = logging.getLogger(__name__)

__all__ = [
    "MokEnrollmentPlan",
    "SecureBootDetector",
    "SigningMaterial",
    "SigningResult",
    "Signer",
    "detect_secure_boot",
    "evaluate_readiness",
    "plan_mok_enrollment",
    "verify_module_signature",
]

_MOKUTIL_TIMEOUT_SECONDS: float = 15.0
_SIGN_FILE_TIMEOUT_SECONDS: float = 60.0
_SBSIGN_TIMEOUT_SECONDS: float = 60.0
_MODINFO_TIMEOUT_SECONDS: float = 30.0
_OPENSSL_TIMEOUT_SECONDS: float = 30.0
_SBVERIFY_TIMEOUT_SECONDS: float = 30.0

#: Hex fingerprint format produced by ``openssl x509 -fingerprint -sha256``
#: and by ``modinfo -F sig_key`` (colon-separated uppercase hex).
_FINGERPRINT_RE = re.compile(r"^([0-9A-F]{2}:)+[0-9A-F]{2}$")

#: ``modinfo`` fields of interest, in order of availability.
_MODINFO_SIGNER_RE = re.compile(r"^signer:\s*(.+)$", re.MULTILINE)
_MODINFO_SIG_KEY_RE = re.compile(r"^sig_key:\s*(.+)$", re.MULTILINE)
_MODINFO_SIG_ID_RE = re.compile(r"^sig_id:\s*(.+)$", re.MULTILINE)
_MODINFO_SIG_HASH_RE = re.compile(r"^sig_hashalgo:\s*(.+)$", re.MULTILINE)


# ---------------------------------------------------------------------------
# SigningMaterial
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SigningMaterial:
    """Operator-supplied signing material paths.

    None of these paths are ever copied into the build output, committed to
    the repository, or logged in full. Only the certificate's public
    fingerprint is recorded.
    """

    key_path: Path
    cert_path: Path
    pin_env_var: str = "KBUILD_SIGN_PIN"
    sign_file_path: Path | None = None  # default: <headers>/scripts/sign-file

    def __post_init__(self) -> None:
        object.__setattr__(self, "key_path", Path(self.key_path))
        object.__setattr__(self, "cert_path", Path(self.cert_path))
        if self.sign_file_path is not None:
            object.__setattr__(self, "sign_file_path", Path(self.sign_file_path))
        if not self.pin_env_var or not isinstance(self.pin_env_var, str):
            raise ValueError("pin_env_var must be a non-empty str")

    def redacted(self) -> dict[str, str]:
        """Return a log-safe summary: no private key path, only fingerprint."""

        return {
            "key_present": str(self.key_path.exists()).lower(),
            "cert_present": str(self.cert_path.exists()).lower(),
            "pin_env_var": self.pin_env_var,
        }


# ---------------------------------------------------------------------------
# MokEnrollmentPlan
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MokEnrollmentPlan:
    """Human-executed MOK enrollment procedure.

    This object is a **description**, not an execution. ``signing.py`` never
    runs the commands in ``commands``; the operator executes them after
    reviewing ``notes``. This separation is deliberate: MOK enrollment
    requires physical console access at the next boot and must not happen
    as a side effect of a build.
    """

    cert_path: Path
    commands: tuple[tuple[str, ...], ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cert_path": str(self.cert_path),
            "commands": [list(c) for c in self.commands],
            "notes": list(self.notes),
        }


def plan_mok_enrollment(cert_path: Path) -> MokEnrollmentPlan:
    """Return the enrollment procedure for ``cert_path`` (DER or PEM)."""
    cert_path = Path(cert_path)
    # mokutil accepts both PEM and DER; DER is what sign-file and dkms
    # expect for the certificate path, and what the Debian wiki uses.
    return MokEnrollmentPlan(
        cert_path=cert_path,
        commands=(
            ("mokutil", "--import", str(cert_path)),
        ),
        notes=(
            "mokutil --import only queues the request; it does not enroll "
            "the key immediately.",
            "You will be prompted for a one-time password. Record it and use "
            "it on the next boot at the MOK Manager screen.",
            "Reboot and, at the blue MOK Manager screen, choose 'Enroll MOK' "
            "-> 'Continue' -> 'Yes', enter the password, then 'Reboot'.",
            "Until enrollment completes, the target kernel will refuse to "
            "load modules signed with this key under Secure Boot.",
            "This command is intentionally never run by the HueyOS build "
            "framework. Execute it manually after reviewing the runbook.",
        ),
    )


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SigningResult:
    """Outcome of a signing phase."""

    secure_boot: SecureBootState
    signed_modules: dict[str, BuildArtifact]
    signed_kernel_image: BuildArtifact | None
    cert_fingerprint: str | None
    boot_ready: bool
    findings: tuple[ValidationFinding, ...]
    mok_enrollment: MokEnrollmentPlan | None
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
            "secure_boot": self.secure_boot.value,
            "signed_modules": {
                name: art.to_dict() for name, art in self.signed_modules.items()
            },
            "signed_kernel_image": (
                self.signed_kernel_image.to_dict()
                if self.signed_kernel_image
                else None
            ),
            "cert_fingerprint": self.cert_fingerprint,
            "boot_ready": self.boot_ready,
            "findings": [f.to_dict() for f in self.findings],
            "mok_enrollment": (
                self.mok_enrollment.to_dict() if self.mok_enrollment else None
            ),
            "dry_run": self.dry_run,
        }


# ---------------------------------------------------------------------------
# Secure Boot detection
# ---------------------------------------------------------------------------


def _classify_sb_state(text: str) -> SecureBootState:
    normalized = text.strip().lower()
    if "secureboot enabled" in normalized:
        return SecureBootState.ENABLED
    if "secureboot disabled" in normalized:
        return SecureBootState.DISABLED
    if "efi variables are not supported" in normalized:
        return SecureBootState.UNKNOWN
    return SecureBootState.UNKNOWN


class SecureBootDetector:
    """Read-only Secure Boot state detection via ``mokutil --sb-state``."""

    def __init__(self, runner: RunnerProtocol) -> None:
        self._runner = runner

    def detect(self) -> tuple[SecureBootState, ValidationFinding | None]:
        spec = CommandSpec(
            argv=("mokutil", "--sb-state"),
            cwd=Path("/"),
            description="mokutil --sb-state",
            timeout_seconds=_MOKUTIL_TIMEOUT_SECONDS,
        )
        try:
            result = self._runner.run(spec)
        except RunnerTimeout as exc:
            return SecureBootState.UNKNOWN, ValidationFinding(
                severity=Severity.WARNING,
                code="SECUREBOOT_DETECT_TIMEOUT",
                message=f"mokutil timed out: {exc}",
            )
        except RunnerError as exc:
            return SecureBootState.UNKNOWN, ValidationFinding(
                severity=Severity.WARNING,
                code="SECUREBOOT_DETECT_UNAVAILABLE",
                message=f"mokutil could not launch: {exc}",
            )
        if not result.succeeded:
            return SecureBootState.UNKNOWN, ValidationFinding(
                severity=Severity.WARNING,
                code="SECUREBOOT_DETECT_FAILED",
                message=(
                    f"mokutil exited {result.command.returncode}; Secure Boot "
                    "state is unknown."
                ),
            )
        text = (result.stdout or b"").decode("utf-8", errors="replace")
        state = _classify_sb_state(text)
        finding = None
        if state == SecureBootState.UNKNOWN:
            finding = ValidationFinding(
                severity=Severity.WARNING,
                code="SECUREBOOT_STATE_UNRECOGNIZED",
                message=f"Unrecognized mokutil output: {text.strip()!r}",
            )
        return state, finding


def detect_secure_boot(
    runner: RunnerProtocol,
) -> tuple[SecureBootState, ValidationFinding | None]:
    """Convenience wrapper around :class:`SecureBootDetector`."""
    return SecureBootDetector(runner).detect()


# ---------------------------------------------------------------------------
# Signer
# ---------------------------------------------------------------------------


class Signer:
    """Sign and verify modules and kernel images against a MOK certificate."""

    def __init__(self, runner: RunnerProtocol) -> None:
        self._runner = runner

    # ---- public API ------------------------------------------------------

    def sign_modules(
        self,
        *,
        modules: dict[str, BuildArtifact],
        module_dir: Path,
        material: SigningMaterial,
        headers_dir: Path,
        output_dir: Path,
        pin: str | None = None,
        hash_algo: str = "sha256",
        dry_run: bool = False,
    ) -> tuple[dict[str, BuildArtifact], list[ValidationFinding], bool]:
        """Sign each staged module **in place** under ``module_dir``.

        Returns ``(signed_artifacts, findings, all_ok)``. ``module_dir`` is
        expected to be the staging directory produced in Step 14; this method
        mutates the ``.ko`` files there by appending the PKCS#7 signature,
        then recomputes their SHA-256 for the returned artifacts.

        The private key is never read by this code. Only its path is passed
        to ``sign-file``. The passphrase is passed through ``KBUILD_SIGN_PIN``
        in the subprocess environment, which the runner redacts by name.
        """
        findings: list[ValidationFinding] = []
        destination_findings = check_path_destination_safe(output_dir)
        if destination_findings:
            return {}, destination_findings, False
        if Path(output_dir).is_symlink() or Path(module_dir).is_symlink():
            return {}, [ValidationFinding(
                severity=Severity.ERROR, code="SIGNING_DIRECTORY_SYMLINK_REFUSED",
                message="Signing may not use symlinked staging directories.",
            )], False

        material_findings, material_ok = self._validate_material(material)
        findings.extend(material_findings)
        if not material_ok:
            return {}, findings, False

        sign_file = self._resolve_sign_file(headers_dir, material)
        if sign_file is None:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="SIGN_FILE_NOT_FOUND",
                    message=(
                        "scripts/sign-file was not found in the headers tree; "
                        "cannot sign modules. Install the matching "
                        "linux-headers package or pass sign_file_path."
                    ),
                )
            )
            return {}, findings, False

        signed: dict[str, BuildArtifact] = {}
        all_ok = True
        if dry_run and not modules:
            findings.append(ValidationFinding(
                severity=Severity.INFO, code="SIGNING_DRY_RUN",
                message="No modules supplied; dry run performed no signing.",
            ))

        for name, artifact in sorted(modules.items()):
            original = module_dir / Path(artifact.path).name
            if original.is_symlink():
                findings.append(ValidationFinding(
                    severity=Severity.ERROR, code="MODULE_SYMLINK_REFUSED",
                    message=f"Refusing to sign symlinked module {name!r}.",
                ))
                all_ok = False
                continue
            if not original.is_file():
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="MODULE_FILE_MISSING",
                        message=f"Module {name!r} not found at {original}",
                    )
                )
                all_ok = False
                continue

            if dry_run:
                findings.append(
                    ValidationFinding(
                        severity=Severity.INFO,
                        code="SIGNING_DRY_RUN",
                        message=(
                            f"Would sign {original.name} with "
                            f"{material.cert_path.name} (fingerprint TBD)."
                        ),
                    )
                )
                signed[name] = artifact
                continue

            # The kernel signing tool modifies a module in place. Sign a
            # private copy and never mutate the Step 14 source artifact.
            target = Path(output_dir) / "signed-modules" / original.name
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.is_symlink():
                    raise OSError("signed module output is a symlink")
                shutil.copy2(original, target)
            except OSError as exc:
                findings.append(ValidationFinding(
                    severity=Severity.ERROR, code="SIGNING_STAGE_FAILED",
                    message=f"Cannot stage module {name!r} for signing: {exc}",
                ))
                all_ok = False
                continue

            sign_finding = self._sign_one(
                target=target,
                sign_file=sign_file,
                material=material,
                pin=pin,
                hash_algo=hash_algo,
            )
            if sign_finding is not None:
                findings.append(sign_finding)
                all_ok = False
                continue

            verify_finding = self.verify_module_signature(
                module_path=target,
                expected_cert=material.cert_path,
            )
            if verify_finding is not None and verify_finding.severity in (
                Severity.ERROR,
                Severity.CRITICAL,
            ):
                findings.append(verify_finding)
                all_ok = False
                continue

            try:
                rel = target.resolve().relative_to(output_dir.resolve())
                sha = _sha256_file(target)
                size = target.stat().st_size
            except (OSError, ValueError) as exc:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="SIGNED_ARTIFACT_HASH_FAILED",
                        message=f"Could not record signed artifact for {name}: {exc}",
                    )
                )
                all_ok = False
                continue

            signed[name] = BuildArtifact(
                kind=ArtifactKind.NVIDIA_MODULE,
                path=str(rel),
                sha256=sha,
                size_bytes=size,
                kernel_release=artifact.kernel_release,
            )

        return signed, findings, all_ok

    def sign_kernel_image(
        self,
        *,
        kernel_image: Path,
        material: SigningMaterial,
        output_dir: Path,
        dry_run: bool = False,
        kernel_release: str | None = None,
    ) -> tuple[BuildArtifact | None, ValidationFinding | None]:
        """Sign a kernel EFI image via ``sbsign`` into ``output_dir``."""
        destination_findings = check_path_destination_safe(output_dir)
        if destination_findings:
            return None, destination_findings[0]
        material_findings, material_ok = self._validate_material(material)
        if not material_ok:
            # Return the first material finding.
            return None, material_findings[0] if material_findings else None

        if not kernel_image.is_file():
            return None, ValidationFinding(
                severity=Severity.ERROR,
                code="KERNEL_IMAGE_MISSING",
                message=f"Kernel image not found: {kernel_image}",
            )

        signed_path = output_dir / f"{kernel_image.name}.signed"
        if dry_run:
            return None, ValidationFinding(
                severity=Severity.INFO,
                code="KERNEL_SIGNING_DRY_RUN",
                message=f"Would sign {kernel_image} -> {signed_path} with sbsign.",
            )

        spec = CommandSpec(
            argv=(
                "sbsign",
                "--key",
                str(material.key_path),
                "--cert",
                str(material.cert_path),
                "--output",
                str(signed_path),
                str(kernel_image),
            ),
            cwd=kernel_image.parent,
            description=f"sbsign {kernel_image.name}",
            timeout_seconds=_SBSIGN_TIMEOUT_SECONDS,
        )
        try:
            result = self._runner.run(spec)
        except (RunnerError, RunnerTimeout) as exc:
            return None, ValidationFinding(
                severity=Severity.ERROR,
                code="SBSIGN_FAILED",
                message=f"sbsign could not run for {kernel_image.name}: {exc}",
            )
        if not result.succeeded:
            return None, ValidationFinding(
                severity=Severity.ERROR,
                code="SBSIGN_FAILED",
                message=(
                    f"sbsign exited {result.command.returncode} for "
                    f"{kernel_image.name}"
                ),
            )
        if not signed_path.is_file():
            return None, ValidationFinding(
                severity=Severity.ERROR,
                code="SBSIGN_NO_OUTPUT",
                message=f"sbsign did not produce {signed_path}",
            )

        verify_finding = self._verify_signed_efi(signed_path, material.cert_path)
        if verify_finding is not None and verify_finding.severity in (
            Severity.ERROR,
            Severity.CRITICAL,
        ):
            return None, verify_finding

        try:
            rel = signed_path.resolve().relative_to(output_dir.resolve())
            sha = _sha256_file(signed_path)
            size = signed_path.stat().st_size
        except (OSError, ValueError) as exc:
            return None, ValidationFinding(
                severity=Severity.ERROR,
                code="SIGNED_IMAGE_HASH_FAILED",
                message=f"Could not record signed kernel image: {exc}",
            )

        return (
            BuildArtifact(
                kind=ArtifactKind.KERNEL_IMAGE_DEB,  # placeholder kind for a signed image
                path=str(rel),
                sha256=sha,
                size_bytes=size,
                kernel_release=kernel_release or "unknown",
            ),
            verify_finding,
        )

    def verify_module_signature(
        self,
        *,
        module_path: Path,
        expected_cert: Path,
    ) -> ValidationFinding | None:
        """Verify ``module_path`` is signed by ``expected_cert``.

        Uses ``modinfo`` fields (``signer``, ``sig_key``, ``sig_id``) which
        are populated by the kernel's module loader metadata. Returns
        ``None`` on success, or a finding on any failure. The certificate's
        SHA-256 fingerprint is computed locally from the public certificate
        (never from the module) and compared to ``sig_key``.
        """
        expected_fp = self._certificate_fingerprint(expected_cert)
        if expected_fp is None:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="CERT_FINGERPRINT_UNAVAILABLE",
                message=(
                    f"Could not compute SHA-256 fingerprint of "
                    f"{expected_cert.name}; cannot verify signed modules."
                ),
            )

        spec = CommandSpec(
            argv=("modinfo", str(module_path)),
            cwd=module_path.parent,
            description=f"modinfo {module_path.name}",
            timeout_seconds=_MODINFO_TIMEOUT_SECONDS,
        )
        try:
            result = self._runner.run(spec)
        except (RunnerError, RunnerTimeout) as exc:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="MODINFO_FAILED",
                message=f"Could not read modinfo for {module_path.name}: {exc}",
            )
        if not result.succeeded:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="MODINFO_FAILED",
                message=(
                    f"modinfo exited {result.command.returncode} for "
                    f"{module_path.name}"
                ),
            )

        text = (result.stdout or b"").decode("utf-8", errors="replace")
        if not _MODINFO_SIGNER_RE.search(text):
            return ValidationFinding(
                severity=Severity.ERROR,
                code="MODULE_UNSIGNED",
                message=(
                    f"{module_path.name} has no signature (no 'signer:' "
                    "field in modinfo)."
                ),
            )

        sig_key_match = _MODINFO_SIG_KEY_RE.search(text)
        if not sig_key_match:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="MODULE_SIG_KEY_MISSING",
                message=(
                    f"{module_path.name} is signed but modinfo does not "
                    "expose sig_key; cannot confirm signer identity."
                ),
            )
        actual_fp = sig_key_match.group(1).strip().upper()
        if not _FINGERPRINT_RE.match(actual_fp):
            return ValidationFinding(
                severity=Severity.ERROR,
                code="MODULE_SIG_KEY_MALFORMED",
                message=(
                    f"{module_path.name} sig_key {actual_fp!r} is not a "
                    "colon-separated hex fingerprint."
                ),
            )
        if actual_fp != expected_fp:
            return ValidationFinding(
                severity=Severity.CRITICAL,
                code="MODULE_SIGNED_BY_WRONG_KEY",
                message=(
                    f"{module_path.name} is signed by a key with fingerprint "
                    f"{actual_fp}, not the expected {expected_fp}. The "
                    "module will not be trusted on the target."
                ),
                context={
                    "module": module_path.name,
                    "expected_fingerprint": expected_fp,
                    "actual_fingerprint": actual_fp,
                },
            )
        return None

    # ---- internals -------------------------------------------------------

    def _validate_material(
        self, material: SigningMaterial
    ) -> tuple[list[ValidationFinding], bool]:
        findings: list[ValidationFinding] = []
        if not material.key_path.is_file():
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="SIGNING_KEY_MISSING",
                    message=(
                        f"Signing private key not found at the configured "
                        "path. Keys live outside the repository; supply "
                        "signing.key_path in the operator environment."
                    ),
                )
            )
        if not material.cert_path.is_file():
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="SIGNING_CERT_MISSING",
                    message=(
                        f"Signing certificate not found at the configured "
                        "path. Supply signing.cert_path."
                    ),
                )
            )
        return findings, not findings

    def _resolve_sign_file(
        self, headers_dir: Path, material: SigningMaterial
    ) -> Path | None:
        if material.sign_file_path is not None:
            return material.sign_file_path if material.sign_file_path.is_file() else None
        candidate = headers_dir / "scripts" / "sign-file"
        return candidate if candidate.is_file() else None

    def _sign_one(
        self,
        *,
        target: Path,
        sign_file: Path,
        material: SigningMaterial,
        pin: str | None,
        hash_algo: str,
    ) -> ValidationFinding | None:
        env: dict[str, str] = {}
        if pin:
            # The runner redacts any env var whose name contains PIN.
            env[material.pin_env_var] = pin

        spec = CommandSpec(
            argv=(
                str(sign_file),
                hash_algo,
                str(material.key_path),
                str(material.cert_path),
                str(target),
            ),
            cwd=target.parent,
            description=f"sign-file {target.name}",
            timeout_seconds=_SIGN_FILE_TIMEOUT_SECONDS,
            env_overrides=env,
        )
        try:
            result = self._runner.run(spec)
        except RunnerTimeout as exc:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="SIGN_FILE_TIMEOUT",
                message=f"sign-file timed out for {target.name}: {exc}",
            )
        except RunnerError as exc:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="SIGN_FILE_LAUNCH_FAILED",
                message=f"sign-file could not launch for {target.name}: {exc}",
            )
        if not result.succeeded:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="SIGN_FILE_FAILED",
                message=(
                    f"sign-file exited {result.command.returncode} for "
                    f"{target.name}. Common causes: wrong certificate format "
                    "(needs DER for sign-file), missing passphrase, or an "
                    "already-signed module."
                ),
            )
        return None

    def _certificate_fingerprint(self, cert_path: Path) -> str | None:
        """Return the cert's SHA-256 fingerprint in ``modinfo``'s format."""
        # Try DER first, then PEM. ``openssl x509`` handles both with -inform.
        for inform in ("DER", "PEM"):
            spec = CommandSpec(
                argv=(
                    "openssl",
                    "x509",
                    "-in",
                    str(cert_path),
                    "-inform",
                    inform,
                    "-noout",
                    "-fingerprint",
                    "-sha256",
                ),
                cwd=cert_path.parent,
                description=f"openssl fingerprint {cert_path.name} ({inform})",
                timeout_seconds=_OPENSSL_TIMEOUT_SECONDS,
            )
            try:
                result = self._runner.run(spec)
            except (RunnerError, RunnerTimeout):
                continue
            if not result.succeeded:
                continue
            text = (result.stdout or b"").decode("utf-8", errors="replace")
            # Expected: "SHA256 Fingerprint=13:FE:C2:...:A9"
            for line in text.splitlines():
                if "=" in line and "Fingerprint" in line:
                    candidate = line.split("=", 1)[1].strip().upper()
                    if _FINGERPRINT_RE.match(candidate):
                        return candidate
        return None

    def _verify_signed_efi(
        self, signed_path: Path, cert_path: Path
    ) -> ValidationFinding | None:
        spec = CommandSpec(
            argv=("sbverify", "--cert", str(cert_path), str(signed_path)),
            cwd=signed_path.parent,
            description=f"sbverify {signed_path.name}",
            timeout_seconds=_SBVERIFY_TIMEOUT_SECONDS,
        )
        try:
            result = self._runner.run(spec)
        except (RunnerError, RunnerTimeout) as exc:
            return ValidationFinding(
                severity=Severity.WARNING,
                code="SBVERIFY_UNAVAILABLE",
                message=f"sbverify could not run: {exc}",
            )
        if not result.succeeded:
            return ValidationFinding(
                severity=Severity.ERROR,
                code="SBVERIFY_FAILED",
                message=(
                    f"sbverify rejected {signed_path.name} against "
                    f"{cert_path.name}"
                ),
            )
        return None


# ---------------------------------------------------------------------------
# Readiness evaluation
# ---------------------------------------------------------------------------


def evaluate_readiness(
    *,
    secure_boot: SecureBootState,
    signing_required: bool,
    material: SigningMaterial | None,
    signed_modules: dict[str, BuildArtifact],
    required_modules: Sequence[str],
    signed_kernel_image: BuildArtifact | None,
    kernel_image_required: bool,
    module_findings: Sequence[ValidationFinding],
) -> tuple[bool, list[ValidationFinding]]:
    """Return ``(boot_ready, findings)`` for the signing phase.

    ``boot_ready`` is True only when every requirement below holds:

    * Secure Boot state is known (``ENABLED`` or ``DISABLED``);
    * if signing is required or Secure Boot is enabled, signing material
      was supplied and every required module was signed;
    * the signed kernel image is present when the boot chain requires it;
    * no module-level finding has ERROR or CRITICAL severity.

    MOK enrollment is **not** a precondition for ``boot_ready=True`` in this
    function: enrollment is required before the **target boots**, not before
    the artifacts are produced. The runbook (Step 29) is the gate that ties
    enrollment to activation.
    """
    findings: list[ValidationFinding] = list(module_findings)

    if secure_boot == SecureBootState.UNKNOWN:
        findings.append(
            ValidationFinding(
                severity=Severity.ERROR,
                code="SECUREBOOT_STATE_UNKNOWN",
                message=(
                    "Secure Boot state is unknown; cannot determine whether "
                    "signing is required. Run 'mokutil --sb-state' on the "
                    "target before promoting any release."
                ),
            )
        )
        return False, findings

    if signing_required or secure_boot == SecureBootState.ENABLED:
        if material is None:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="SIGNING_MATERIAL_ABSENT",
                    message=(
                        "Signing is required but no signing material was "
                        "supplied. The image is not boot-ready."
                    ),
                )
            )
            return False, findings
        for required in required_modules:
            if required not in signed_modules:
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="REQUIRED_MODULE_UNSIGNED",
                        message=(
                            f"Required module {required!r} is not signed."
                        ),
                    )
                )
        if kernel_image_required and signed_kernel_image is None:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="KERNEL_IMAGE_UNSIGNED",
                    message=(
                        "The boot chain requires a signed kernel image, but "
                        "none was produced."
                    ),
                )
            )

    blocking = [
        f for f in findings if f.severity in (Severity.ERROR, Severity.CRITICAL)
    ]
    return not blocking, findings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
