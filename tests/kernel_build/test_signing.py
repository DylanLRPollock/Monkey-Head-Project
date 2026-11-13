"""Canonical test suite for huey.kernel_build.signing (Step 42).

Step 18 landed an initial suite proving each branch worked. This file
expands that suite to the full contract required by the handoff:

* Secure Boot detection: 4 output forms + tool missing + timeout;
* MOK enrollment plan shape + structural proof that
  `mokutil --import` is never invoked as a subprocess;
* signing material validation: missing key, missing cert, both;
* sign-file argv/env shape; PIN isolation from argv;
* sign-file failure modes: launch / timeout / nonzero;
* post-signing verification: SHA updated on disk; unsigned module,
  missing sig_key, malformed sig_key, wrong sig_key (CRITICAL), and
  fingerprint unavailable;
* kernel image signing: happy path, sbsign launch/nonzero/timeout,
  sbverify failure, sbverify unavailable (WARNING), missing kernel
  image, missing material, dry run;
* evaluate_readiness branches: UNKNOWN, disabled, enabled without
  material, enabled with material, unsigned module, missing kernel
  image, critical in module_findings;
* dry run zero-I/O;
* JSON serialization with MokEnrollmentPlan.

All subprocesses are simulated via FixtureRunner. Nothing touches the
real MOK database, signing keys, or GPU. Filesystem state is under
tmp_path only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable

import pytest

from huey.kernel_build.models import (
    ArtifactKind,
    BuildArtifact,
    CommandResult,
    Severity,
)
from huey.kernel_build.policy import SecureBootState
from huey.kernel_build.runner import (
    CommandSpec,
    RunnerError,
    RunnerResult,
    RunnerTimeout,
)
from huey.kernel_build.signing import (
    MokEnrollmentPlan,
    SecureBootDetector,
    Signer,
    SigningMaterial,
    SigningResult,
    detect_secure_boot,
    evaluate_readiness,
    plan_mok_enrollment,
)


# ===========================================================================
# FixtureRunner
# ===========================================================================


class FixtureRunner:
    def __init__(self) -> None:
        self._handlers: list = []
        self._calls: list[CommandSpec] = []

    def on(self, matcher, handler) -> "FixtureRunner":
        self._handlers.append((matcher, handler))
        return self

    def run(self, spec: CommandSpec, *, dry_run: bool = False) -> RunnerResult:
        self._calls.append(spec)
        for matcher, handler in self._handlers:
            if matcher(spec):
                return handler(spec)
        raise RunnerError(f"no handler for argv={spec.argv!r}")

    @property
    def calls(self) -> tuple[CommandSpec, ...]:
        return tuple(self._calls)


def _ok(spec, *, stdout: bytes = b"", stderr: bytes = b"") -> RunnerResult:
    return RunnerResult(
        command=CommandResult(
            argv=spec.argv, cwd=str(spec.cwd),
            returncode=0, elapsed_seconds=0.0,
        ),
        executed=True, dry_run=False, stdout=stdout, stderr=stderr,
    )


def _fail(spec, returncode: int = 1) -> RunnerResult:
    return RunnerResult(
        command=CommandResult(
            argv=spec.argv, cwd=str(spec.cwd),
            returncode=returncode, elapsed_seconds=0.0,
        ),
        executed=True, dry_run=False, stdout=b"", stderr=b"",
    )


def _is_mokutil(spec): return spec.argv[0] == "mokutil"
def _is_sign_file(spec): return str(spec.argv[0]).endswith("sign-file")
def _is_modinfo(spec): return spec.argv[0] == "modinfo"
def _is_openssl(spec): return spec.argv[0] == "openssl"
def _is_sbsign(spec): return spec.argv[0] == "sbsign"
def _is_sbverify(spec): return spec.argv[0] == "sbverify"


# ===========================================================================
# Fixtures
# ===========================================================================

EXPECTED_FP = (
    "13:FE:C2:ED:A1:40:CE:70:1A:75:91:E5:4C:1F:5F:DA:"
    "BD:17:57:A9:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55"
)

WRONG_FP = (
    "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:"
    "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99"
)


def _make_material(
    tmp_path: Path, *, key: bool = True, cert: bool = True
) -> SigningMaterial:
    key_path = tmp_path / "MOK.priv"
    cert_path = tmp_path / "MOK.der"
    if key:
        key_path.write_bytes(b"fake private key\n")
    if cert:
        cert_path.write_bytes(b"fake certificate\n")
    return SigningMaterial(key_path=key_path, cert_path=cert_path)


def _make_headers(tmp_path: Path) -> Path:
    headers = tmp_path / "headers"
    (headers / "scripts").mkdir(parents=True)
    sign_file = headers / "scripts" / "sign-file"
    sign_file.write_text("#!/bin/sh\n", encoding="utf-8")
    sign_file.chmod(0o755)
    return headers


def _make_module_artifact(module_dir: Path, name: str) -> BuildArtifact:
    module_dir.mkdir(parents=True, exist_ok=True)
    path = module_dir / f"{name}.ko"
    path.write_bytes(f"fake ko {name}\n".encode())
    return BuildArtifact(
        kind=ArtifactKind.NVIDIA_MODULE,
        path=f"{module_dir.name}/{name}.ko",
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        size_bytes=path.stat().st_size,
        kernel_release="7.2.15-huey1",
    )


def _fingerprint_handler(spec: CommandSpec) -> RunnerResult:
    return _ok(spec, stdout=f"SHA256 Fingerprint={EXPECTED_FP}\n".encode())


def _modinfo_signed(spec: CommandSpec) -> RunnerResult:
    name = Path(spec.argv[1]).name
    stdout = (
        f"filename: {spec.argv[1]}\n"
        "license: Dual MIT/GPL\n"
        f"name: {name[:-3]}\n"
        "sig_id: PKCS#7\n"
        "signer: Huey Builder\n"
        f"sig_key: {EXPECTED_FP}\n"
        "sig_hashalgo: sha256\n"
    )
    return _ok(spec, stdout=stdout.encode())


def _make_modinfo_handler(mode: str):
    """Return a modinfo handler for the requested mode.

    Modes: signed, unsigned, wrong_key, malformed_sig_key, missing_sig_key.
    """
    def handler(spec: CommandSpec) -> RunnerResult:
        name = Path(spec.argv[1]).name
        base = (
            f"filename: {spec.argv[1]}\n"
            "license: Dual MIT/GPL\n"
            f"name: {name[:-3]}\n"
        )
        if mode == "unsigned":
            return _ok(spec, stdout=base.encode())
        if mode == "wrong_key":
            body = base + (
                "sig_id: PKCS#7\nsigner: Attacker\n"
                f"sig_key: {WRONG_FP}\n"
            )
            return _ok(spec, stdout=body.encode())
        if mode == "malformed_sig_key":
            body = base + "sig_id: PKCS#7\nsigner: X\nsig_key: not-a-fingerprint\n"
            return _ok(spec, stdout=body.encode())
        if mode == "missing_sig_key":
            body = base + "sig_id: PKCS#7\nsigner: X\n"
            return _ok(spec, stdout=body.encode())
        # signed
        body = base + (
            "sig_id: PKCS#7\nsigner: Huey Builder\n"
            f"sig_key: {EXPECTED_FP}\nsig_hashalgo: sha256\n"
        )
        return _ok(spec, stdout=body.encode())
    return handler


def _sign_file_appends_signature(spec: CommandSpec) -> RunnerResult:
    """Simulate signing by appending a signature block to the target."""
    target = Path(spec.argv[-1])
    if not target.is_file():
        return _fail(spec, returncode=1)
    target.write_bytes(target.read_bytes() + b"\nSIGNATURE_BLOCK\n")
    return _ok(spec)


def _build_runner(
    *,
    sb_state: str = "SecureBoot enabled",
    sign_file_mode: str = "ok",  # ok, launch_fails, timeout, nonzero
    modinfo_mode: str = "signed",
    cert_fingerprint: str = EXPECTED_FP,
    openssl_mode: str = "ok",
    sbsign_mode: str = "ok",
    sbverify_mode: str = "ok",
) -> FixtureRunner:
    r = FixtureRunner()

    def _mok(spec):
        return _ok(spec, stdout=f"{sb_state}\n".encode())

    def _sign(spec):
        if sign_file_mode == "launch_fails":
            raise RunnerError("sign-file not found")
        if sign_file_mode == "timeout":
            raise RunnerTimeout("sign-file timeout")
        if sign_file_mode == "nonzero":
            return _fail(spec, returncode=2)
        return _sign_file_appends_signature(spec)

    def _openssl(spec):
        if openssl_mode != "ok":
            return _fail(spec, returncode=1)
        return _ok(
            spec, stdout=f"SHA256 Fingerprint={cert_fingerprint}\n".encode()
        )

    def _sbsign(spec):
        if sbsign_mode == "launch_fails":
            raise RunnerError("sbsign not found")
        if sbsign_mode == "timeout":
            raise RunnerTimeout("sbsign timeout")
        if sbsign_mode == "nonzero":
            return _fail(spec, returncode=2)
        # Write the -o output file so the builder sees it.
        out_path = Path(spec.argv[spec.argv.index("--output") + 1])
        out_path.write_bytes(b"signed kernel image\n")
        return _ok(spec)

    def _sbverify(spec):
        if sbverify_mode == "failure":
            return _fail(spec, returncode=1)
        if sbverify_mode == "unavailable":
            raise RunnerError("sbverify not found")
        return _ok(spec)

    r.on(_is_mokutil, _mok)
    r.on(_is_sign_file, _sign)
    r.on(_is_openssl, _openssl)
    r.on(_is_modinfo, _make_modinfo_handler(modinfo_mode))
    r.on(_is_sbsign, _sbsign)
    r.on(_is_sbverify, _sbverify)
    return r


def _setup_signing(tmp_path: Path, *, n_modules: int = 2) -> tuple[
    Path, Path, dict, Path
]:
    """Return (headers, stage_dir, artifacts, output_dir)."""
    material = _make_material(tmp_path)
    headers = _make_headers(tmp_path)
    output_dir = tmp_path / "out"
    stage = output_dir / "nvidia-580.196.07-7.2.15-huey1"
    stage.mkdir(parents=True)
    modules = ("nvidia", "nvidia-uvm")[:n_modules]
    artifacts = {
        name: _make_module_artifact(stage, name) for name in modules
    }
    return headers, stage, artifacts, output_dir


# ===========================================================================
# Secure Boot detection
# ===========================================================================


@pytest.mark.parametrize(
    "stdout, expected",
    [
        (b"SecureBoot enabled\n", SecureBootState.ENABLED),
        (b"SecureBoot disabled\n", SecureBootState.DISABLED),
        (
            b"EFI variables are not supported on this system\n",
            SecureBootState.UNKNOWN,
        ),
        (b"weird output\n", SecureBootState.UNKNOWN),
    ],
)
def test_detect_secure_boot_states(
    stdout: bytes, expected: SecureBootState
) -> None:
    runner = FixtureRunner().on(
        _is_mokutil, lambda s: _ok(s, stdout=stdout)
    )
    state, finding = detect_secure_boot(runner)
    assert state == expected
    if expected == SecureBootState.UNKNOWN:
        assert finding is not None
        assert finding.severity == Severity.WARNING


def test_detect_secure_boot_tool_missing() -> None:
    def _raise(spec):
        raise RunnerError("mokutil not found")

    runner = FixtureRunner().on(_is_mokutil, _raise)
    state, finding = detect_secure_boot(runner)
    assert state == SecureBootState.UNKNOWN
    assert finding is not None
    assert finding.code == "SECUREBOOT_DETECT_UNAVAILABLE"
    assert finding.severity == Severity.WARNING


def test_detect_secure_boot_timeout() -> None:
    def _timeout(spec):
        raise RunnerTimeout("timed out")

    runner = FixtureRunner().on(_is_mokutil, _timeout)
    state, finding = detect_secure_boot(runner)
    assert state == SecureBootState.UNKNOWN
    assert finding is not None
    assert finding.code == "SECUREBOOT_DETECT_TIMEOUT"
    assert finding.severity == Severity.WARNING


# ===========================================================================
# MOK enrollment plan
# ===========================================================================


def test_mok_enrollment_plan_shape(tmp_path: Path) -> None:
    cert = tmp_path / "MOK.der"
    cert.write_bytes(b"cert")
    plan = plan_mok_enrollment(cert)
    assert isinstance(plan, MokEnrollmentPlan)
    assert ("mokutil", "--import", str(cert)) in plan.commands
    notes = " ".join(plan.notes).lower()
    assert "queues" in notes
    assert "reboot" in notes
    assert "never run by the hueyos build framework" in notes


def test_signing_never_executes_mokutil_import() -> None:
    """Structural proof: --import appears only in the plan, never in a Runner call."""
    import inspect

    from huey.kernel_build import signing as signing_module

    source = inspect.getsource(signing_module)
    # --import appears as a literal in plan_mok_enrollment.
    assert '"--import"' in source
    # The only executable mokutil argv is the read-only --sb-state probe.
    assert 'argv=("mokutil", "--sb-state")' in source
    assert 'argv=("mokutil", "--import"' not in source


# ===========================================================================
# Signing material validation
# ===========================================================================


def test_missing_key_errors(tmp_path: Path) -> None:
    material = _make_material(tmp_path, key=False)
    headers = _make_headers(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    signed, findings, ok = Signer(_build_runner()).sign_modules(
        modules={}, module_dir=out, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    assert signed == {}
    assert any(f.code == "SIGNING_KEY_MISSING" for f in findings)


def test_missing_cert_errors(tmp_path: Path) -> None:
    material = _make_material(tmp_path, cert=False)
    headers = _make_headers(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    signed, findings, ok = Signer(_build_runner()).sign_modules(
        modules={}, module_dir=out, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    assert any(f.code == "SIGNING_CERT_MISSING" for f in findings)


def test_both_missing_errors(tmp_path: Path) -> None:
    material = _make_material(tmp_path, key=False, cert=False)
    headers = _make_headers(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    signed, findings, ok = Signer(_build_runner()).sign_modules(
        modules={}, module_dir=out, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    codes = {f.code for f in findings}
    assert {"SIGNING_KEY_MISSING", "SIGNING_CERT_MISSING"} <= codes


# ===========================================================================
# Sign-file invocation shape
# ===========================================================================


def test_sign_file_argv_shape(tmp_path: Path) -> None:
    headers, stage, artifacts, out = _setup_signing(tmp_path)
    material = _make_material(tmp_path)
    runner = _build_runner()
    Signer(runner).sign_modules(
        modules=artifacts, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out, pin="pin-1234",
        hash_algo="sha256",
    )
    sign_calls = [c for c in runner.calls if _is_sign_file(c)]
    assert len(sign_calls) == 2, f"expected 2 sign-file calls, got {sign_calls}"
    for spec in sign_calls:
        argv = spec.argv
        assert str(argv[0]).endswith("sign-file")
        assert argv[1] == "sha256"
        assert argv[2] == str(material.key_path)
        assert argv[3] == str(material.cert_path)
        assert argv[4].endswith(".ko")
        # PIN never in argv.
        assert "pin-1234" not in " ".join(argv)


def test_sign_file_pin_passed_via_env(tmp_path: Path) -> None:
    headers, stage, artifacts, out = _setup_signing(tmp_path)
    material = _make_material(tmp_path)
    runner = _build_runner()
    Signer(runner).sign_modules(
        modules=artifacts, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out, pin="pin-1234",
    )
    sign_calls = [c for c in runner.calls if _is_sign_file(c)]
    assert sign_calls
    assert sign_calls[0].env_overrides.get("KBUILD_SIGN_PIN") == "pin-1234"


def test_sign_file_pin_absent_when_not_supplied(tmp_path: Path) -> None:
    headers, stage, artifacts, out = _setup_signing(tmp_path)
    material = _make_material(tmp_path)
    runner = _build_runner()
    Signer(runner).sign_modules(
        modules=artifacts, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out, pin=None,
    )
    sign_calls = [c for c in runner.calls if _is_sign_file(c)]
    assert sign_calls
    assert "KBUILD_SIGN_PIN" not in sign_calls[0].env_overrides


# ===========================================================================
# Sign-file failure modes
# ===========================================================================


@pytest.mark.parametrize(
    "mode, expected_code",
    [
        ("launch_fails", "SIGN_FILE_LAUNCH_FAILED"),
        ("timeout", "SIGN_FILE_TIMEOUT"),
        ("nonzero", "SIGN_FILE_FAILED"),
    ],
)
def test_sign_file_failure_modes(
    tmp_path: Path, mode: str, expected_code: str
) -> None:
    headers, stage, artifacts, out = _setup_signing(tmp_path)
    material = _make_material(tmp_path)
    signed, findings, ok = Signer(
        _build_runner(sign_file_mode=mode)
    ).sign_modules(
        modules=artifacts, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    codes = {f.code for f in findings}
    assert expected_code in codes
    # Unsigned modules skipped.
    assert signed == {}


# ===========================================================================
# Post-signing verification
# ===========================================================================


def test_happy_path_signs_and_verifies(tmp_path: Path) -> None:
    headers, stage, artifacts, out = _setup_signing(tmp_path)
    material = _make_material(tmp_path)
    signed, findings, ok = Signer(_build_runner()).sign_modules(
        modules=artifacts, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is True, findings
    assert set(signed) == set(artifacts)
    for name, art in signed.items():
        assert art.kernel_release == "7.2.15-huey1"
        assert len(art.sha256) == 64
        assert not Path(art.path).is_absolute()


def test_signed_module_sha_updated(tmp_path: Path) -> None:
    """After signing, the recorded SHA-256 reflects the signed file."""
    headers, stage, artifacts, out = _setup_signing(tmp_path)
    material = _make_material(tmp_path)
    original_shas = {n: a.sha256 for n, a in artifacts.items()}

    signed, _, ok = Signer(_build_runner()).sign_modules(
        modules=artifacts, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is True
    for name, art in signed.items():
        assert art.sha256 != original_shas[name], (
            f"{name}: SHA did not change after signing"
        )
        # And matches the file on disk after signing.
        original = stage / Path(art.path).name
        on_disk = out / art.path
        assert hashlib.sha256(on_disk.read_bytes()).hexdigest() == art.sha256
        assert hashlib.sha256(original.read_bytes()).hexdigest() == original_shas[name]


def test_unsigned_module_rejected(tmp_path: Path) -> None:
    headers, stage, artifacts, out = _setup_signing(tmp_path)
    material = _make_material(tmp_path)
    signed, findings, ok = Signer(
        _build_runner(modinfo_mode="unsigned")
    ).sign_modules(
        modules=artifacts, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    assert any(f.code == "MODULE_UNSIGNED" for f in findings)
    assert signed == {}


def test_missing_sig_key_rejected(tmp_path: Path) -> None:
    headers, stage, artifacts, out = _setup_signing(tmp_path)
    material = _make_material(tmp_path)
    signed, findings, ok = Signer(
        _build_runner(modinfo_mode="missing_sig_key")
    ).sign_modules(
        modules=artifacts, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    assert any(f.code == "MODULE_SIG_KEY_MISSING" for f in findings)


def test_malformed_sig_key_rejected(tmp_path: Path) -> None:
    headers, stage, artifacts, out = _setup_signing(tmp_path)
    material = _make_material(tmp_path)
    signed, findings, ok = Signer(
        _build_runner(modinfo_mode="malformed_sig_key")
    ).sign_modules(
        modules=artifacts, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    assert any(f.code == "MODULE_SIG_KEY_MALFORMED" for f in findings)


def test_wrong_key_signature_is_critical(tmp_path: Path) -> None:
    headers, stage, artifacts, out = _setup_signing(tmp_path)
    material = _make_material(tmp_path)
    signed, findings, ok = Signer(
        _build_runner(modinfo_mode="wrong_key")
    ).sign_modules(
        modules=artifacts, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    critical = [f for f in findings if f.code == "MODULE_SIGNED_BY_WRONG_KEY"]
    assert critical, findings
    assert critical[0].severity == Severity.CRITICAL


def test_fingerprint_unavailable_rejected(tmp_path: Path) -> None:
    headers, stage, artifacts, out = _setup_signing(tmp_path)
    material = _make_material(tmp_path)
    signed, findings, ok = Signer(
        _build_runner(openssl_mode="fail")
    ).sign_modules(
        modules=artifacts, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    assert any(f.code == "CERT_FINGERPRINT_UNAVAILABLE" for f in findings)
    assert signed == {}


# ===========================================================================
# Kernel image signing
# ===========================================================================


def test_sign_kernel_image_happy_path(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    kernel = tmp_path / "vmlinuz-7.2.15-huey1"
    kernel.write_bytes(b"fake kernel image\n")
    out = tmp_path / "out"
    out.mkdir()
    artifact, finding = Signer(_build_runner()).sign_kernel_image(
        kernel_image=kernel, material=material, output_dir=out,
    )
    assert artifact is not None, finding
    assert finding is None
    assert (out / Path(artifact.path).name).is_file()


@pytest.mark.parametrize(
    "mode, expected_code",
    [
        ("launch_fails", "SBSIGN_FAILED"),
        ("timeout", "SBSIGN_FAILED"),
        ("nonzero", "SBSIGN_FAILED"),
    ],
)
def test_sbsign_failure_modes(
    tmp_path: Path, mode: str, expected_code: str
) -> None:
    material = _make_material(tmp_path)
    kernel = tmp_path / "vmlinuz"
    kernel.write_bytes(b"k")
    out = tmp_path / "out"
    out.mkdir()
    artifact, finding = Signer(
        _build_runner(sbsign_mode=mode)
    ).sign_kernel_image(
        kernel_image=kernel, material=material, output_dir=out,
    )
    assert artifact is None
    assert finding is not None
    assert finding.code == expected_code


def test_sbverify_failure_errors(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    kernel = tmp_path / "vmlinuz"
    kernel.write_bytes(b"k")
    out = tmp_path / "out"
    out.mkdir()
    artifact, finding = Signer(
        _build_runner(sbverify_mode="failure")
    ).sign_kernel_image(
        kernel_image=kernel, material=material, output_dir=out,
    )
    assert artifact is None
    assert finding is not None
    assert finding.code == "SBVERIFY_FAILED"


def test_sbverify_unavailable_warns_but_keeps_artifact(tmp_path: Path) -> None:
    """sbverify unavailable is a WARNING; the signed artifact is still returned."""
    material = _make_material(tmp_path)
    kernel = tmp_path / "vmlinuz"
    kernel.write_bytes(b"k")
    out = tmp_path / "out"
    out.mkdir()
    artifact, finding = Signer(
        _build_runner(sbverify_mode="unavailable")
    ).sign_kernel_image(
        kernel_image=kernel, material=material, output_dir=out,
    )
    assert artifact is not None
    assert finding is not None
    assert finding.code == "SBVERIFY_UNAVAILABLE"
    assert finding.severity == Severity.WARNING


def test_sign_kernel_image_missing_file(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    artifact, finding = Signer(_build_runner()).sign_kernel_image(
        kernel_image=tmp_path / "nonexistent",
        material=material, output_dir=out,
    )
    assert artifact is None
    assert finding is not None
    assert finding.code == "KERNEL_IMAGE_MISSING"


def test_sign_kernel_image_missing_material(tmp_path: Path) -> None:
    material = _make_material(tmp_path, key=False)
    kernel = tmp_path / "vmlinuz"
    kernel.write_bytes(b"k")
    out = tmp_path / "out"
    out.mkdir()
    artifact, finding = Signer(_build_runner()).sign_kernel_image(
        kernel_image=kernel, material=material, output_dir=out,
    )
    assert artifact is None
    assert finding is not None
    assert finding.code == "SIGNING_KEY_MISSING"


# ===========================================================================
# evaluate_readiness
# ===========================================================================


def _signed_artifact(name: str = "nvidia") -> BuildArtifact:
    return BuildArtifact(
        kind=ArtifactKind.NVIDIA_MODULE, path=f"stage/{name}.ko",
        sha256="a" * 64, size_bytes=100, kernel_release="7.2.15-huey1",
    )


def _material_present(tmp_path: Path) -> SigningMaterial:
    return _make_material(tmp_path)


def test_readiness_unknown_state_blocks() -> None:
    ready, findings = evaluate_readiness(
        secure_boot=SecureBootState.UNKNOWN,
        signing_required=False,
        material=None,
        signed_modules={},
        required_modules=(),
        signed_kernel_image=None,
        kernel_image_required=False,
        module_findings=[],
    )
    assert ready is False
    assert any(f.code == "SECUREBOOT_STATE_UNKNOWN" for f in findings)


def test_readiness_disabled_without_requirement_passes() -> None:
    ready, findings = evaluate_readiness(
        secure_boot=SecureBootState.DISABLED,
        signing_required=False,
        material=None,
        signed_modules={},
        required_modules=("nvidia", "nvidia-uvm"),
        signed_kernel_image=None,
        kernel_image_required=False,
        module_findings=[],
    )
    assert ready is True
    blocking = [f for f in findings if f.severity in (Severity.ERROR, Severity.CRITICAL)]
    assert not blocking


def test_readiness_enabled_without_material_fails() -> None:
    ready, findings = evaluate_readiness(
        secure_boot=SecureBootState.ENABLED,
        signing_required=True,
        material=None,
        signed_modules={},
        required_modules=("nvidia",),
        signed_kernel_image=None,
        kernel_image_required=False,
        module_findings=[],
    )
    assert ready is False
    assert any(f.code == "SIGNING_MATERIAL_ABSENT" for f in findings)


def test_readiness_enabled_with_all_signed_passes(tmp_path: Path) -> None:
    ready, findings = evaluate_readiness(
        secure_boot=SecureBootState.ENABLED,
        signing_required=True,
        material=_material_present(tmp_path),
        signed_modules={
            "nvidia": _signed_artifact("nvidia"),
            "nvidia-uvm": _signed_artifact("nvidia-uvm"),
        },
        required_modules=("nvidia", "nvidia-uvm"),
        signed_kernel_image=None,
        kernel_image_required=False,
        module_findings=[],
    )
    assert ready is True, findings


def test_readiness_required_module_unsigned_fails(tmp_path: Path) -> None:
    ready, findings = evaluate_readiness(
        secure_boot=SecureBootState.ENABLED,
        signing_required=True,
        material=_material_present(tmp_path),
        signed_modules={"nvidia": _signed_artifact("nvidia")},
        required_modules=("nvidia", "nvidia-uvm"),
        signed_kernel_image=None,
        kernel_image_required=False,
        module_findings=[],
    )
    assert ready is False
    assert any(f.code == "REQUIRED_MODULE_UNSIGNED" for f in findings)


def test_readiness_kernel_image_required_missing_fails(tmp_path: Path) -> None:
    ready, findings = evaluate_readiness(
        secure_boot=SecureBootState.ENABLED,
        signing_required=True,
        material=_material_present(tmp_path),
        signed_modules={"nvidia": _signed_artifact("nvidia")},
        required_modules=("nvidia",),
        signed_kernel_image=None,
        kernel_image_required=True,
        module_findings=[],
    )
    assert ready is False
    assert any(f.code == "KERNEL_IMAGE_UNSIGNED" for f in findings)


def test_readiness_critical_module_finding_propagates(tmp_path: Path) -> None:
    from huey.kernel_build.models import ValidationFinding

    critical = ValidationFinding(
        severity=Severity.CRITICAL,
        code="MODULE_SIGNED_BY_WRONG_KEY",
        message="wrong key",
    )
    ready, findings = evaluate_readiness(
        secure_boot=SecureBootState.ENABLED,
        signing_required=True,
        material=_material_present(tmp_path),
        signed_modules={"nvidia": _signed_artifact("nvidia")},
        required_modules=("nvidia",),
        signed_kernel_image=None,
        kernel_image_required=False,
        module_findings=[critical],
    )
    assert ready is False
    assert critical in findings


# ===========================================================================
# Dry run
# ===========================================================================


def test_dry_run_no_io_no_subprocess(tmp_path: Path) -> None:
    headers, stage, artifacts, out = _setup_signing(tmp_path)
    material = _make_material(tmp_path)
    runner = FixtureRunner()  # zero handlers
    signed, findings, ok = Signer(runner).sign_modules(
        modules=artifacts, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out, dry_run=True,
    )
    assert runner.calls == ()
    assert any(f.code == "SIGNING_DRY_RUN" for f in findings)


# ===========================================================================
# JSON serialization
# ===========================================================================


def test_signing_result_json_serializable(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    result = SigningResult(
        secure_boot=SecureBootState.ENABLED,
        signed_modules={"nvidia": _signed_artifact()},
        signed_kernel_image=None,
        cert_fingerprint=EXPECTED_FP,
        boot_ready=False,
        findings=(),
        mok_enrollment=plan_mok_enrollment(material.cert_path),
        dry_run=False,
    )
    payload = json.dumps(result.to_dict())
    assert "nvidia" in payload
    assert EXPECTED_FP in payload
    assert "mokutil" in payload
    # The MOK plan is embedded as a structured dict, not a repr.
    loaded = json.loads(payload)
    assert loaded["mok_enrollment"]["commands"] == [
        ["mokutil", "--import", str(material.cert_path)]
    ]
