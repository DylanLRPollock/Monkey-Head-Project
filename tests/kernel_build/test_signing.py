"""Tests for huey.kernel_build.signing (Step 18; Step 42 expands).

All tests offline. ``mokutil``, ``sign-file``, ``modinfo``, ``openssl``,
``sbsign``, and ``sbverify`` are simulated via ``FixtureRunner``. Private
keys and PINs are represented as tiny fixture files; no real key material
is present and no crypto operation is executed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

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


# ---------------------------------------------------------------------------
# FixtureRunner
# ---------------------------------------------------------------------------


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


def _ok(spec, *, stdout: bytes = b"") -> RunnerResult:
    return RunnerResult(
        command=CommandResult(
            argv=spec.argv, cwd=str(spec.cwd),
            returncode=0, elapsed_seconds=0.0,
        ),
        executed=True, dry_run=False, stdout=stdout, stderr=b"",
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
def _is_sign_file(spec): return str(spec.argv[0]).endswith("scripts/sign-file")
def _is_modinfo(spec): return spec.argv[0] == "modinfo"
def _is_openssl(spec): return spec.argv[0] == "openssl"
def _is_sbsign(spec): return spec.argv[0] == "sbsign"
def _is_sbverify(spec): return spec.argv[0] == "sbverify"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

EXPECTED_FP = "13:FE:C2:ED:A1:40:CE:70:1A:75:91:E5:4C:1F:5F:DA:BD:17:57:A9:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55"


def _make_material(tmp_path: Path, *, key: bool = True, cert: bool = True) -> SigningMaterial:
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
        path=f"nvidia-580.196.07-7.2.15-huey1/{name}.ko",
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


def _build_runner(
    *,
    sb_state: str = "SecureBoot enabled",
    sign_file_returncode: int = 0,
    modinfo_unsigned: bool = False,
    modinfo_wrong_key: bool = False,
    cert_fingerprint: str = EXPECTED_FP,
    sbverify_ok: bool = True,
) -> FixtureRunner:
    r = FixtureRunner()

    def _mok(spec):
        return _ok(spec, stdout=f"{sb_state}\n".encode())

    def _sign(spec):
        return _ok(spec) if sign_file_returncode == 0 else _fail(spec, sign_file_returncode)

    def _openssl_fp(spec):
        return _ok(spec, stdout=f"SHA256 Fingerprint={cert_fingerprint}\n".encode())

    def _modinfo(spec):
        if modinfo_unsigned:
            return _ok(spec, stdout=b"filename: x\nname: nvidia\n")
        if modinfo_wrong_key:
            return _ok(spec, stdout=(
                "sig_id: PKCS#7\nsigner: Attacker\nsig_key: "
                "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:"
                "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99\n"
            ).encode())
        return _modinfo_signed(spec)

    def _sbsign(spec):
        idx = spec.argv.index("--output")
        Path(spec.argv[idx + 1]).write_bytes(b"signed kernel image\n")
        return _ok(spec)

    def _sbverify(spec):
        return _ok(spec) if sbverify_ok else _fail(spec, returncode=1)

    r.on(_is_mokutil, _mok)
    r.on(_is_sign_file, _sign)
    r.on(_is_openssl, _openssl_fp)
    r.on(_is_modinfo, _modinfo)
    r.on(_is_sbsign, _sbsign)
    r.on(_is_sbverify, _sbverify)
    return r


# ---------------------------------------------------------------------------
# Secure Boot detection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        ("SecureBoot enabled", SecureBootState.ENABLED),
        ("SecureBoot disabled", SecureBootState.DISABLED),
        ("EFI variables are not supported on this system", SecureBootState.UNKNOWN),
        ("weird output", SecureBootState.UNKNOWN),
    ],
)
def test_detect_secure_boot_states(text: str, expected: SecureBootState) -> None:
    runner = FixtureRunner().on(_is_mokutil, lambda s: _ok(s, stdout=f"{text}\n".encode()))
    state, finding = detect_secure_boot(runner)
    assert state == expected
    if expected == SecureBootState.UNKNOWN:
        assert finding is not None and finding.severity == Severity.WARNING


def test_detect_secure_boot_tool_missing() -> None:
    def _raise(spec):
        raise RunnerError("mokutil not found")

    runner = FixtureRunner().on(_is_mokutil, _raise)
    state, finding = detect_secure_boot(runner)
    assert state == SecureBootState.UNKNOWN
    assert finding is not None and "could not launch" in finding.message


# ---------------------------------------------------------------------------
# MOK enrollment plan (documented, never executed)
# ---------------------------------------------------------------------------


def test_mok_enrollment_plan_is_descriptive(tmp_path: Path) -> None:
    cert = tmp_path / "MOK.der"
    cert.write_bytes(b"cert")
    plan = plan_mok_enrollment(cert)
    assert isinstance(plan, MokEnrollmentPlan)
    assert ("mokutil", "--import", str(cert)) in plan.commands
    notes = " ".join(plan.notes).lower()
    assert "queues" in notes
    assert "reboot" in notes
    assert "never run by the hueyos build framework" in notes


def test_signer_never_calls_mokutil_import(tmp_path: Path) -> None:
    """Structural proof: enrollment is not automated."""
    import inspect

    from huey.kernel_build import signing as signing_module

    source = inspect.getsource(signing_module)
    assert '"--import"' in source  # documented in plan_mok_enrollment
    # But no code path invokes mokutil --import: the only mokutil argv is
    # the read-only --sb-state probe.
    assert 'argv=("mokutil", "--sb-state")' in source
    assert 'argv=("mokutil", "--import"' not in source


# ---------------------------------------------------------------------------
# Happy path: sign + verify modules
# ---------------------------------------------------------------------------


def test_sign_modules_happy_path(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    headers = _make_headers(tmp_path)
    module_dir = tmp_path / "staging"
    artifacts = {
        "nvidia": _make_module_artifact(module_dir, "nvidia"),
        "nvidia-uvm": _make_module_artifact(module_dir, "nvidia-uvm"),
    }
    out = tmp_path / "out"
    out.mkdir()
    # Place staged modules under out so relative path computation works.
    stage = out / "nvidia-580.196.07-7.2.15-huey1"
    stage.mkdir()
    for name in ("nvidia", "nvidia-uvm"):
        (stage / f"{name}.ko").write_bytes(f"fake ko {name}\n".encode())
    artifacts = {
        name: BuildArtifact(
            kind=ArtifactKind.NVIDIA_MODULE,
            path=f"{stage.name}/{name}.ko",
            sha256=hashlib.sha256((stage / f"{name}.ko").read_bytes()).hexdigest(),
            size_bytes=(stage / f"{name}.ko").stat().st_size,
            kernel_release="7.2.15-huey1",
        )
        for name in ("nvidia", "nvidia-uvm")
    }

    signed, findings, ok = Signer(_build_runner()).sign_modules(
        modules=artifacts,
        module_dir=stage,
        material=material,
        headers_dir=headers,
        output_dir=out,
        pin="secret-pin",
    )
    assert ok is True, findings
    assert set(signed) == {"nvidia", "nvidia-uvm"}
    for name, art in signed.items():
        assert art.kernel_release == "7.2.15-huey1"
        assert len(art.sha256) == 64
        assert not Path(art.path).is_absolute()


def test_sign_modules_pin_never_appears_in_argv(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    headers = _make_headers(tmp_path)
    out = tmp_path / "out"; out.mkdir()
    stage = out / "stage"; stage.mkdir()
    (stage / "nvidia.ko").write_bytes(b"ko\n")
    art = BuildArtifact(
        kind=ArtifactKind.NVIDIA_MODULE, path="stage/nvidia.ko",
        sha256="a" * 64, size_bytes=3, kernel_release="7.2.15-huey1",
    )
    runner = _build_runner()
    Signer(runner).sign_modules(
        modules={"nvidia": art}, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out, pin="super-secret",
    )
    # The PIN must not appear in any argv.
    for call in runner.calls:
        assert "super-secret" not in " ".join(call.argv)
    # But it must be passed via the env var.
    sign_calls = [c for c in runner.calls if _is_sign_file(c)]
    assert sign_calls, "sign-file was not invoked"
    assert sign_calls[0].env_overrides.get("KBUILD_SIGN_PIN") == "super-secret"


# ---------------------------------------------------------------------------
# Signing material validation
# ---------------------------------------------------------------------------


def test_missing_key_errors(tmp_path: Path) -> None:
    material = _make_material(tmp_path, key=False)
    headers = _make_headers(tmp_path)
    out = tmp_path / "out"; out.mkdir()
    signed, findings, ok = Signer(_build_runner()).sign_modules(
        modules={}, module_dir=out, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    assert any(f.code == "SIGNING_KEY_MISSING" for f in findings)


def test_missing_cert_errors(tmp_path: Path) -> None:
    material = _make_material(tmp_path, cert=False)
    headers = _make_headers(tmp_path)
    out = tmp_path / "out"; out.mkdir()
    signed, findings, ok = Signer(_build_runner()).sign_modules(
        modules={}, module_dir=out, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    assert any(f.code == "SIGNING_CERT_MISSING" for f in findings)


def test_missing_sign_file_errors(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    headers = tmp_path / "headers"
    headers.mkdir()  # no scripts/sign-file
    out = tmp_path / "out"; out.mkdir()
    signed, findings, ok = Signer(_build_runner()).sign_modules(
        modules={}, module_dir=out, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    assert any(f.code == "SIGN_FILE_NOT_FOUND" for f in findings)


# ---------------------------------------------------------------------------
# Verification failures
# ---------------------------------------------------------------------------


def test_unsigned_module_is_rejected(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    headers = _make_headers(tmp_path)
    out = tmp_path / "out"; out.mkdir()
    stage = out / "stage"; stage.mkdir()
    (stage / "nvidia.ko").write_bytes(b"ko\n")
    art = BuildArtifact(
        kind=ArtifactKind.NVIDIA_MODULE, path="stage/nvidia.ko",
        sha256="a" * 64, size_bytes=3, kernel_release="7.2.15-huey1",
    )
    signed, findings, ok = Signer(
        _build_runner(modinfo_unsigned=True)
    ).sign_modules(
        modules={"nvidia": art}, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    assert any(f.code == "MODULE_UNSIGNED" for f in findings)


def test_wrong_key_signature_is_critical(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    headers = _make_headers(tmp_path)
    out = tmp_path / "out"; out.mkdir()
    stage = out / "stage"; stage.mkdir()
    (stage / "nvidia.ko").write_bytes(b"ko\n")
    art = BuildArtifact(
        kind=ArtifactKind.NVIDIA_MODULE, path="stage/nvidia.ko",
        sha256="a" * 64, size_bytes=3, kernel_release="7.2.15-huey1",
    )
    signed, findings, ok = Signer(
        _build_runner(modinfo_wrong_key=True)
    ).sign_modules(
        modules={"nvidia": art}, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    critical = [f for f in findings if f.code == "MODULE_SIGNED_BY_WRONG_KEY"]
    assert critical and critical[0].severity == Severity.CRITICAL


def test_sign_file_failure_errors(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    headers = _make_headers(tmp_path)
    out = tmp_path / "out"; out.mkdir()
    stage = out / "stage"; stage.mkdir()
    (stage / "nvidia.ko").write_bytes(b"ko\n")
    art = BuildArtifact(
        kind=ArtifactKind.NVIDIA_MODULE, path="stage/nvidia.ko",
        sha256="a" * 64, size_bytes=3, kernel_release="7.2.15-huey1",
    )
    signed, findings, ok = Signer(
        _build_runner(sign_file_returncode=2)
    ).sign_modules(
        modules={"nvidia": art}, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok is False
    assert any(f.code == "SIGN_FILE_FAILED" for f in findings)


# ---------------------------------------------------------------------------
# Kernel image signing
# ---------------------------------------------------------------------------


def test_sign_kernel_image_happy_path(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    kernel = tmp_path / "vmlinuz-7.2.15-huey1"
    kernel.write_bytes(b"fake kernel image\n")
    out = tmp_path / "out"; out.mkdir()
    artifact, finding = Signer(_build_runner()).sign_kernel_image(
        kernel_image=kernel, material=material, output_dir=out,
    )
    assert finding is None or finding.severity == Severity.INFO, finding
    assert artifact is not None
    assert (out / Path(artifact.path).name).is_file()


def test_sbsign_failure_errors(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    kernel = tmp_path / "vmlinuz"; kernel.write_bytes(b"k")
    out = tmp_path / "out"; out.mkdir()
    runner = FixtureRunner()
    runner.on(_is_sbsign, lambda s: _fail(s, returncode=1))
    artifact, finding = Signer(runner).sign_kernel_image(
        kernel_image=kernel, material=material, output_dir=out,
    )
    assert artifact is None
    assert finding is not None and finding.code == "SBSIGN_FAILED"


def test_sbverify_failure_errors(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    kernel = tmp_path / "vmlinuz"; kernel.write_bytes(b"k")
    out = tmp_path / "out"; out.mkdir()
    artifact, finding = Signer(_build_runner(sbverify_ok=False)).sign_kernel_image(
        kernel_image=kernel, material=material, output_dir=out,
    )
    assert artifact is None
    assert finding is not None and finding.code == "SBVERIFY_FAILED"


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


def test_sign_modules_dry_run_no_io_no_subprocess(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    headers = _make_headers(tmp_path)
    out = tmp_path / "out"; out.mkdir()
    runner = FixtureRunner()  # no handlers
    signed, findings, ok = Signer(runner).sign_modules(
        modules={}, module_dir=out, material=material,
        headers_dir=headers, output_dir=out, dry_run=True,
    )
    assert runner.calls == ()
    assert any(f.code == "SIGNING_DRY_RUN" for f in findings)


# ---------------------------------------------------------------------------
# Readiness
# ---------------------------------------------------------------------------


def _signed_artifact(name: str = "nvidia") -> BuildArtifact:
    return BuildArtifact(
        kind=ArtifactKind.NVIDIA_MODULE, path=f"stage/{name}.ko",
        sha256="a" * 64, size_bytes=3, kernel_release="7.2.15-huey1",
    )


def test_readiness_secure_boot_disabled_no_signing_required() -> None:
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
    assert not [f for f in findings if f.severity in (Severity.ERROR, Severity.CRITICAL)]


def test_readiness_secure_boot_enabled_missing_material() -> None:
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


def test_readiness_secure_boot_enabled_all_signed() -> None:
    material = SigningMaterial(Path("/k"), Path("/c"))
    ready, findings = evaluate_readiness(
        secure_boot=SecureBootState.ENABLED,
        signing_required=True,
        material=material,
        signed_modules={"nvidia": _signed_artifact(), "nvidia-uvm": _signed_artifact("nvidia-uvm")},
        required_modules=("nvidia", "nvidia-uvm"),
        signed_kernel_image=None,
        kernel_image_required=False,
        module_findings=[],
    )
    assert ready is True, findings


def test_readiness_required_module_unsigned() -> None:
    material = SigningMaterial(Path("/k"), Path("/c"))
    ready, findings = evaluate_readiness(
        secure_boot=SecureBootState.ENABLED,
        signing_required=True,
        material=material,
        signed_modules={"nvidia": _signed_artifact()},
        required_modules=("nvidia", "nvidia-uvm"),
        signed_kernel_image=None,
        kernel_image_required=False,
        module_findings=[],
    )
    assert ready is False
    assert any(f.code == "REQUIRED_MODULE_UNSIGNED" for f in findings)


def test_readiness_kernel_image_required_missing() -> None:
    material = SigningMaterial(Path("/k"), Path("/c"))
    ready, findings = evaluate_readiness(
        secure_boot=SecureBootState.ENABLED,
        signing_required=True,
        material=material,
        signed_modules={"nvidia": _signed_artifact()},
        required_modules=("nvidia",),
        signed_kernel_image=None,
        kernel_image_required=True,
        module_findings=[],
    )
    assert ready is False
    assert any(f.code == "KERNEL_IMAGE_UNSIGNED" for f in findings)


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


# ---------------------------------------------------------------------------
# JSON serialization
# ---------------------------------------------------------------------------


def test_signing_result_is_json_serializable(tmp_path: Path) -> None:
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


# Security regressions: do not sign the original module file in place.
def test_signing_stages_private_copy_without_altering_original(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    headers = _make_headers(tmp_path)
    out = tmp_path / "out"; out.mkdir()
    stage = out / "stage"; stage.mkdir()
    art = _make_module_artifact(stage, "nvidia")
    original = stage / "nvidia.ko"
    before = original.read_bytes()
    signed, findings, ok = Signer(_build_runner()).sign_modules(
        modules={"nvidia": art}, module_dir=stage, material=material,
        headers_dir=headers, output_dir=out,
    )
    assert ok, findings
    assert original.read_bytes() == before
    assert signed["nvidia"].path == "signed-modules/nvidia.ko"
    assert (out / signed["nvidia"].path).is_file()


def test_signing_rejects_protected_output(tmp_path: Path) -> None:
    material = _make_material(tmp_path)
    headers = _make_headers(tmp_path)
    signed, findings, ok = Signer(_build_runner()).sign_modules(
        modules={}, module_dir=tmp_path, material=material,
        headers_dir=headers, output_dir=Path("/boot/huey-signing"),
    )
    assert not ok
    assert any(f.code == "PROTECTED_HOST_PATH" for f in findings)
