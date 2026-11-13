"""Tests for huey.kernel_build.inventory (Step 7; Step 36 expands).

All tests run offline: subprocesses are stubbed via a ``FixtureRunner`` that
dispatches by argv prefix, and filesystem reads go through ``FakeHostFs``
pointed at a per-test ``tmp_path``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pytest

from huey.kernel_build.models import (
    GPUVendor,
    ModuleFlavor,
    Severity,
)
from huey.kernel_build.inventory import (
    FakeHostFs,
    HostInventory,
    InventoryReport,
    collect_inventory,
)
from huey.kernel_build.policy import SecureBootState
from huey.kernel_build.runner import (
    CommandSpec,
    DRY_RUN_RETURNCODE,
    RunnerError,
    RunnerResult,
    RunnerTimeout,
)
from huey.kernel_build.models import CommandResult


# ---------------------------------------------------------------------------
# FixtureRunner: dispatch by argv prefix
# ---------------------------------------------------------------------------


def _result(
    argv: tuple[str, ...],
    *,
    stdout: bytes = b"",
    stderr: bytes = b"",
    returncode: int = 0,
    cwd: str = "/",
) -> RunnerResult:
    return RunnerResult(
        command=CommandResult(
            argv=argv,
            cwd=cwd,
            returncode=returncode,
            elapsed_seconds=0.0,
        ),
        executed=True,
        dry_run=False,
        stdout=stdout,
        stderr=stderr,
    )


class FixtureRunner:
    """Runner that matches commands by argv prefix."""

    def __init__(self) -> None:
        self._handlers: dict[tuple[str, ...], Callable[[CommandSpec], RunnerResult]] = {}
        self._calls: list[CommandSpec] = []

    def on(
        self, prefix: tuple[str, ...], handler: Callable[[CommandSpec], RunnerResult]
    ) -> "FixtureRunner":
        self._handlers[prefix] = handler
        return self

    def run(self, spec: CommandSpec, *, dry_run: bool = False) -> RunnerResult:
        self._calls.append(spec)
        for prefix in sorted(self._handlers, key=len, reverse=True):
            if spec.argv[: len(prefix)] == prefix:
                return self._handlers[prefix](spec)
        raise RunnerError(f"FixtureRunner: no handler for argv={spec.argv!r}")

    @property
    def calls(self) -> tuple[CommandSpec, ...]:
        return tuple(self._calls)


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------


def _fixed_clock() -> datetime:
    return datetime(2026, 11, 12, 8, 0, 0, tzinfo=timezone.utc)


def _populate_fake_fs(
    root: Path,
    *,
    configs: tuple[str, ...] = ("7.2.12+deb14-amd64", "7.2.15+deb14-amd64"),
    headers: tuple[str, ...] = ("7.2.12+deb14-amd64", "7.2.15+deb14-amd64"),
    os_release: bool = True,
) -> None:
    if os_release:
        (root / "etc").mkdir(parents=True, exist_ok=True)
        (root / "etc" / "os-release").write_text(
            'NAME="Debian GNU/Linux"\n'
            'VERSION_ID="forky"\n'
            'PRETTY_NAME="Debian GNU/Linux forky/sid"\n',
            encoding="utf-8",
        )
    boot = root / "boot"
    boot.mkdir(parents=True, exist_ok=True)
    for cfg in configs:
        (boot / f"config-{cfg}").write_text("CONFIG_X=y\n", encoding="utf-8")
    modules = root / "lib" / "modules"
    modules.mkdir(parents=True, exist_ok=True)
    for hdr in headers:
        build = modules / hdr / "build"
        build.mkdir(parents=True)


def _nvidia_csv_two_gpus() -> bytes:
    # V100 first, RX 570 absent from nvidia-smi (it is AMD)
    return (
        b"Tesla V100-PCIE-32GB, GPU-11111111-1111-1111-1111-111111111111, "
        b"00000000:01:00.0, 7.0\n"
        b"Tesla V100-PCIE-32GB, GPU-22222222-2222-2222-2222-222222222222, "
        b"00000000:03:00.0, 7.0\n"
    )


def _nvidia_banner() -> bytes:
    return (
        b"| NVIDIA-SMI 580.196.07   Driver Version: 580.196.07   "
        b"CUDA Version: 13.0     |\n"
    )


def _lspci_full() -> bytes:
    return (
        b"0000:01:00.0 VGA compatible controller [0300]: NVIDIA Corporation "
        b"GV100GL [Tesla V100 PCIe 32GB] [10de:1db6] (rev a1)\n"
        b"0000:02:00.0 VGA compatible controller [0300]: Advanced Micro Devices, "
        b"Inc. [AMD/ATI] Ellesmere [Radeon RX 470/480/570/570X/580/580X/590] "
        b"[1002:67df] (rev ef)\n"
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def _build_happy_path_runner() -> FixtureRunner:
    return (
        FixtureRunner()
        .on(("uname", "-r"), lambda s: _result(s.argv, stdout=b"7.2.15+deb14-amd64\n"))
        .on(("mokutil", "--sb-state"), lambda s: _result(s.argv, stdout=b"SecureBoot disabled\n"))
        .on(
            ("nvidia-smi", "--query-gpu=name,uuid,pci.bus_id,compute_cap"),
            lambda s: _result(s.argv, stdout=_nvidia_csv_two_gpus()),
        )
        .on(
            ("nvidia-smi", "--query-gpu=driver_version"),
            lambda s: _result(s.argv, stdout=b"580.196.07\n"),
        )
        .on(("nvidia-smi",), lambda s: _result(s.argv, stdout=_nvidia_banner()))
        .on(("lspci", "-nnk"), lambda s: _result(s.argv, stdout=_lspci_full()))
        .on(("modinfo", "-F", "version", "nvidia"), lambda s: _result(s.argv, stdout=b"580.196.07\n"))
        .on(
            ("dkms", "status"),
            lambda s: _result(
                s.argv,
                stdout=(
                    b"nvidia/580.196.07, 7.2.12+deb14-amd64, x86_64: installed\n"
                    b"nvidia/580.196.07, 7.2.15+deb14-amd64, x86_64: installed\n"
                ),
            ),
        )
        .on(("nvcc", "--version"), lambda s: _result(s.argv, stdout=(
            b"nvcc: NVIDIA (R) Cuda compiler driver\n"
            b"Cuda compilation tools, release 12.9, V12.9.86\n"
        )))
    )


def test_happy_path_collects_all_fields(tmp_path: Path) -> None:
    _populate_fake_fs(tmp_path)
    fs = FakeHostFs(tmp_path)
    runner = _build_happy_path_runner()
    report = HostInventory(runner, host_fs=fs, clock=_fixed_clock).collect()

    assert isinstance(report, InventoryReport)
    assert report.running_kernel == "7.2.15+deb14-amd64"
    assert report.secure_boot == SecureBootState.DISABLED
    assert report.os_release.get("NAME") == "Debian GNU/Linux"
    assert report.os_release.get("VERSION_ID") == "forky"
    assert report.collected_at == "2026-11-12T08:00:00Z"

    # Driver baseline
    assert report.driver is not None
    assert report.driver.driver_version == "580.196.07"
    assert report.driver.module_flavor == ModuleFlavor.PROPRIETARY
    assert report.driver.cuda_api_version == "13.0"
    assert report.driver.cuda_toolkit_version == "12.9"
    assert report.driver.dkms_builds == (
        "7.2.12+deb14-amd64",
        "7.2.15+deb14-amd64",
    )

    # GPU identities: V100 (from nvidia-smi) + RX 570 (from lspci)
    vendors = {g.vendor for g in report.gpus}
    assert GPUVendor.NVIDIA in vendors
    assert GPUVendor.AMD in vendors
    v100 = [g for g in report.gpus if g.compute_capability == "sm_70"]
    assert len(v100) == 2
    for g in v100:
        assert g.vendor == GPUVendor.NVIDIA
        assert g.uuid is not None and g.uuid.startswith("GPU-")
    rx570 = [g for g in report.gpus if g.vendor == GPUVendor.AMD]
    assert len(rx570) == 1
    assert rx570[0].pci_address == "00000000:02:00.0"

    # Kernel artifacts
    assert report.kernel_configs_available == (
        "7.2.12+deb14-amd64",
        "7.2.15+deb14-amd64",
    )
    assert report.kernel_headers_available == (
        "7.2.12+deb14-amd64",
        "7.2.15+deb14-amd64",
    )

    # nvcc
    assert report.nvcc_version == "12.9"

    # No blocking findings for a clean happy path
    assert not report.has_blocking_findings()


def test_report_is_json_serializable(tmp_path: Path) -> None:
    _populate_fake_fs(tmp_path)
    fs = FakeHostFs(tmp_path)
    runner = _build_happy_path_runner()
    report = HostInventory(runner, host_fs=fs, clock=_fixed_clock).collect()
    serialized = json.dumps(report.to_dict())
    assert "Tesla V100-PCIE-32GB" in serialized
    assert "580.196.07" in serialized
    assert "sm_70" in serialized


# ---------------------------------------------------------------------------
# CUDA API vs installed toolkit: distinct fields
# ---------------------------------------------------------------------------


def test_cuda_api_vs_toolkit_are_distinct(tmp_path: Path) -> None:
    """nvidia-smi's CUDA Version and nvcc's release must be separate values."""
    _populate_fake_fs(tmp_path)
    report = HostInventory(
        _build_happy_path_runner(), host_fs=FakeHostFs(tmp_path), clock=_fixed_clock
    ).collect()
    assert report.driver is not None
    assert report.driver.cuda_api_version == "13.0"
    assert report.driver.cuda_toolkit_version == "12.9"
    assert report.driver.cuda_api_version != report.driver.cuda_toolkit_version


# ---------------------------------------------------------------------------
# Missing tools -> graceful, no exceptions
# ---------------------------------------------------------------------------


def _all_missing_runner() -> FixtureRunner:
    """Every handler raises RunnerError; simulates a sparse host."""
    runner = FixtureRunner()

    def _raise(spec: CommandSpec) -> RunnerResult:
        raise RunnerError(f"{spec.argv[0]} not found")

    runner.on(("uname",), _raise)
    runner.on(("mokutil",), _raise)
    runner.on(("nvidia-smi",), _raise)
    runner.on(("lspci",), _raise)
    runner.on(("modinfo",), _raise)
    runner.on(("/usr/sbin/modinfo",), _raise)
    runner.on(("/sbin/modinfo",), _raise)
    runner.on(("dkms",), _raise)
    runner.on(("nvcc",), _raise)
    runner.on(("/usr/local/cuda/bin/nvcc",), _raise)
    runner.on(("/usr/bin/nvcc",), _raise)
    return runner


def test_missing_tools_do_not_raise(tmp_path: Path) -> None:
    # No files created -> os-release, /boot, /lib/modules all absent
    fs = FakeHostFs(tmp_path)
    report = HostInventory(_all_missing_runner(), host_fs=fs, clock=_fixed_clock).collect()

    assert report.running_kernel is None
    assert report.secure_boot == SecureBootState.UNKNOWN
    assert report.gpus == ()
    assert report.driver is None
    assert report.dkms_status_lines == ()
    assert report.dkms_kernel_releases_for_driver == ()
    assert report.nvcc_version is None
    assert report.kernel_configs_available == ()
    assert report.kernel_headers_available == ()

    # Findings cover the critical absences
    codes = {f.code for f in report.findings}
    assert "UNAME_UNAVAILABLE" in codes
    assert "SECUREBOOT_STATE_UNKNOWN" in codes
    assert "NVIDIA_SMI_UNAVAILABLE" in codes
    assert "LSPCI_UNAVAILABLE" in codes
    assert "MODINFO_NVIDIA_UNAVAILABLE" in codes
    assert "DKMS_STATUS_UNAVAILABLE" in codes
    assert "NVCC_UNAVAILABLE" in codes
    # No blocking findings for read-only absence
    assert not report.has_blocking_findings()


def test_command_timeout_is_a_warning(tmp_path: Path) -> None:
    runner = FixtureRunner()

    def _timeout(spec: CommandSpec) -> RunnerResult:
        raise RunnerTimeout("timed out")

    runner.on(("uname",), _timeout)
    runner.on(("mokutil",), _timeout)
    runner.on(("nvidia-smi",), _timeout)
    runner.on(("lspci",), _timeout)
    runner.on(("modinfo",), _timeout)
    runner.on(("dkms",), _timeout)
    runner.on(("nvcc",), _timeout)

    report = HostInventory(runner, host_fs=FakeHostFs(tmp_path), clock=_fixed_clock).collect()
    warning_codes = {f.code for f in report.findings if f.severity == Severity.WARNING}
    assert "UNAME_UNAVAILABLE" in warning_codes


# ---------------------------------------------------------------------------
# Two GPU outputs and index-independence
# ---------------------------------------------------------------------------


def test_two_gpu_ordering_does_not_affect_identity(tmp_path: Path) -> None:
    """V100 at index 1 (second row) still has correct PCI/UUID."""
    _populate_fake_fs(tmp_path)
    runner = FixtureRunner()
    runner.on(("uname", "-r"), lambda s: _result(s.argv, stdout=b"7.2.15+deb14-amd64\n"))
    runner.on(("mokutil", "--sb-state"), lambda s: _result(s.argv, stdout=b"SecureBoot disabled\n"))
    runner.on(
        ("nvidia-smi", "--query-gpu=name,uuid,pci.bus_id,compute_cap"),
        lambda s: _result(
            s.argv,
            stdout=(
                b"Tesla V100-PCIE-32GB, GPU-BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB, "
                b"00000000:0b:00.0, 7.0\n"
                b"Tesla V100-PCIE-32GB, GPU-AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA, "
                b"00000000:0a:00.0, 7.0\n"
            ),
        ),
    )
    runner.on(
        ("nvidia-smi", "--query-gpu=driver_version"),
        lambda s: _result(s.argv, stdout=b"580.196.07\n"),
    )
    runner.on(("nvidia-smi",), lambda s: _result(s.argv, stdout=_nvidia_banner()))
    runner.on(("lspci", "-nnk"), lambda s: _result(s.argv, stdout=b""))
    runner.on(("modinfo", "-F", "version", "nvidia"), lambda s: _result(s.argv, stdout=b"580.196.07\n"))
    runner.on(("dkms", "status"), lambda s: _result(s.argv, stdout=b""))
    runner.on(("nvcc", "--version"), lambda s: _result(s.argv, stdout=b"release 12.9\n"))

    report = HostInventory(runner, host_fs=FakeHostFs(tmp_path), clock=_fixed_clock).collect()
    v100 = sorted(
        (g for g in report.gpus if g.compute_capability == "sm_70"),
        key=lambda g: g.pci_address,
    )
    assert [g.pci_address for g in v100] == [
        "00000000:0a:00.0",
        "00000000:0b:00.0",
    ]
    # Identifiers come from PCI/UUID, not index
    assert v100[0].uuid == "GPU-AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"
    assert v100[1].uuid == "GPU-BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB"


# ---------------------------------------------------------------------------
# Secure Boot state variants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stdout, expected",
    [
        (b"SecureBoot enabled\n", SecureBootState.ENABLED),
        (b"SecureBoot disabled\n", SecureBootState.DISABLED),
        (b"EFI variables are not supported on this system\n", SecureBootState.UNKNOWN),
        (b"weird output\n", SecureBootState.UNKNOWN),
    ],
)
def test_secure_boot_states(stdout: bytes, expected: SecureBootState, tmp_path: Path) -> None:
    _populate_fake_fs(tmp_path)
    runner = FixtureRunner()
    runner.on(("uname", "-r"), lambda s: _result(s.argv, stdout=b"7.2.15+deb14-amd64\n"))
    runner.on(("mokutil", "--sb-state"), lambda s: _result(s.argv, stdout=stdout))
    runner.on(("nvidia-smi",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("lspci",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("modinfo",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("dkms",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("nvcc",), lambda s: _result(s.argv, stdout=b""))
    report = HostInventory(runner, host_fs=FakeHostFs(tmp_path), clock=_fixed_clock).collect()
    assert report.secure_boot == expected


# ---------------------------------------------------------------------------
# Kernel headers mismatch
# ---------------------------------------------------------------------------


def test_running_kernel_no_headers_triggers_warning(tmp_path: Path) -> None:
    """Running kernel X, headers only for Y -> WARNING."""
    _populate_fake_fs(
        tmp_path,
        configs=("7.2.12+deb14-amd64",),
        headers=("7.2.12+deb14-amd64",),
    )
    runner = FixtureRunner()
    runner.on(("uname", "-r"), lambda s: _result(s.argv, stdout=b"7.2.99-huey1\n"))
    runner.on(("mokutil", "--sb-state"), lambda s: _result(s.argv, stdout=b"SecureBoot disabled\n"))
    runner.on(("nvidia-smi",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("lspci",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("modinfo",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("dkms",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("nvcc",), lambda s: _result(s.argv, stdout=b""))
    report = HostInventory(runner, host_fs=FakeHostFs(tmp_path), clock=_fixed_clock).collect()
    codes = {f.code for f in report.findings}
    assert "RUNNING_KERNEL_NO_HEADERS" in codes
    assert not report.has_blocking_findings()  # warning only


# ---------------------------------------------------------------------------
# Driver version mismatch between nvidia-smi and modinfo
# ---------------------------------------------------------------------------


def test_driver_version_mismatch_warns(tmp_path: Path) -> None:
    _populate_fake_fs(tmp_path)
    runner = FixtureRunner()
    runner.on(("uname", "-r"), lambda s: _result(s.argv, stdout=b"7.2.15+deb14-amd64\n"))
    runner.on(("mokutil", "--sb-state"), lambda s: _result(s.argv, stdout=b"SecureBoot disabled\n"))
    runner.on(("nvidia-smi", "--query-gpu=name,uuid,pci.bus_id,compute_cap"), lambda s: _result(s.argv, stdout=b""))
    runner.on(("nvidia-smi", "--query-gpu=driver_version"), lambda s: _result(s.argv, stdout=b"580.196.07\n"))
    runner.on(("nvidia-smi",), lambda s: _result(s.argv, stdout=_nvidia_banner()))
    runner.on(("lspci",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("modinfo", "-F", "version", "nvidia"), lambda s: _result(s.argv, stdout=b"580.100.00\n"))
    runner.on(("dkms",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("nvcc",), lambda s: _result(s.argv, stdout=b""))
    report = HostInventory(runner, host_fs=FakeHostFs(tmp_path), clock=_fixed_clock).collect()
    codes = {f.code for f in report.findings}
    assert "DRIVER_VERSION_MISMATCH" in codes


# ---------------------------------------------------------------------------
# DKMS kernel release filtering
# ---------------------------------------------------------------------------


def test_dkms_filters_by_driver_version(tmp_path: Path) -> None:
    _populate_fake_fs(tmp_path)
    runner = _build_happy_path_runner()
    # Override dkms status with a different driver version and a stale entry
    runner.on(
        ("dkms", "status"),
        lambda s: _result(
            s.argv,
            stdout=(
                b"nvidia/580.196.07, 7.2.15+deb14-amd64, x86_64: installed\n"
                b"nvidia/550.100.00, 7.2.12+deb14-amd64, x86_64: installed\n"
            ),
        ),
    )
    report = HostInventory(runner, host_fs=FakeHostFs(tmp_path), clock=_fixed_clock).collect()
    assert report.dkms_kernel_releases_for_driver == ("7.2.15+deb14-amd64",)
    # But the raw lines still include both
    assert any("550.100.00" in line for line in report.dkms_status_lines)


def test_dkms_no_match_for_driver_version_warns(tmp_path: Path) -> None:
    _populate_fake_fs(tmp_path)
    runner = _build_happy_path_runner()
    runner.on(
        ("dkms", "status"),
        lambda s: _result(
            s.argv,
            stdout=b"nvidia/550.100.00, 7.2.12+deb14-amd64, x86_64: installed\n",
        ),
    )
    report = HostInventory(runner, host_fs=FakeHostFs(tmp_path), clock=_fixed_clock).collect()
    codes = {f.code for f in report.findings}
    assert "DKMS_DRIVER_VERSION_MISMATCH" in codes
    assert report.dkms_kernel_releases_for_driver == ()


# ---------------------------------------------------------------------------
# Open module detection
# ---------------------------------------------------------------------------


def test_open_module_in_dkms_is_flagged(tmp_path: Path) -> None:
    _populate_fake_fs(tmp_path)
    runner = _build_happy_path_runner()
    runner.on(
        ("dkms", "status"),
        lambda s: _result(
            s.argv,
            stdout=b"nvidia-open/580.196.07, 7.2.15+deb14-amd64, x86_64: installed\n",
        ),
    )
    report = HostInventory(runner, host_fs=FakeHostFs(tmp_path), clock=_fixed_clock).collect()
    assert report.driver is not None
    assert report.driver.module_flavor == ModuleFlavor.OPEN
    codes = {f.code for f in report.findings}
    assert "OPEN_MODULE_IN_DKMS" in codes


def test_proprietary_inference_warns(tmp_path: Path) -> None:
    """Normal case: flavor inferred as proprietary with a WARNING."""
    _populate_fake_fs(tmp_path)
    report = HostInventory(
        _build_happy_path_runner(), host_fs=FakeHostFs(tmp_path), clock=_fixed_clock
    ).collect()
    codes = {f.code for f in report.findings}
    assert "MODULE_FLAVOR_INFERRED_PROPRIETARY" in codes
    assert report.driver is not None
    assert report.driver.module_flavor == ModuleFlavor.PROPRIETARY


# ---------------------------------------------------------------------------
# Convenience function and no host mutation
# ---------------------------------------------------------------------------


def test_collect_inventory_convenience(tmp_path: Path) -> None:
    _populate_fake_fs(tmp_path)
    report = collect_inventory(
        _build_happy_path_runner(), host_fs=FakeHostFs(tmp_path)
    )
    assert isinstance(report, InventoryReport)
    assert report.running_kernel == "7.2.15+deb14-amd64"


def test_inventory_makes_no_write_calls(tmp_path: Path) -> None:
    """FakeHostFs exposes no write API; this is a contract test."""
    fs = FakeHostFs(tmp_path)
    # The protocol has only read_text / list_dir / exists.
    assert hasattr(fs, "read_text")
    assert hasattr(fs, "list_dir")
    assert hasattr(fs, "exists")
    # No write / mkdir / unlink helpers on the injected FS.
    for forbidden in ("write_text", "write_bytes", "mkdir", "unlink"):
        assert not hasattr(fs, forbidden), (
            f"FakeHostFs must not expose {forbidden!r}: inventory must be read-only"
        )


# ---------------------------------------------------------------------------
# modinfo fallback path
# ---------------------------------------------------------------------------


def test_modinfo_uses_fallback_path_when_path_missing(tmp_path: Path) -> None:
    _populate_fake_fs(tmp_path)
    runner = FixtureRunner()
    runner.on(("uname", "-r"), lambda s: _result(s.argv, stdout=b"7.2.15+deb14-amd64\n"))
    runner.on(("mokutil", "--sb-state"), lambda s: _result(s.argv, stdout=b"SecureBoot disabled\n"))
    runner.on(("nvidia-smi",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("lspci",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("modinfo", "-F", "version", "nvidia"), lambda s: (_ for _ in ()).throw(RunnerError("no modinfo")))
    runner.on(("/usr/sbin/modinfo", "-F", "version", "nvidia"), lambda s: _result(s.argv, stdout=b"580.196.07\n"))
    runner.on(("dkms",), lambda s: _result(s.argv, stdout=b""))
    runner.on(("nvcc",), lambda s: _result(s.argv, stdout=b""))
    report = HostInventory(runner, host_fs=FakeHostFs(tmp_path), clock=_fixed_clock).collect()
    # Driver baseline comes from modinfo because nvidia-smi was absent
    assert report.driver is not None
    assert report.driver.driver_version == "580.196.07"
