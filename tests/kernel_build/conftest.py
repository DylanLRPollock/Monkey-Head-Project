"""Shared pytest fixtures for tests/kernel_build (Step 32).

Design contract
---------------
* **Offline only.** No fixture launches a subprocess unless the test requests
  it explicitly through a fixture that names that intent. In particular, the
  fake_runner fixture's default behavior is to raise ``RunnerError`` on any
  unhandled call. Fail-closed.
* **No privileged host state.** No fixture reads or writes ``/boot``,
  ``/lib/modules``, ``/etc``, DKMS, the running kernel, or the GPU. Every
  fixture that touches the filesystem uses the pytest-provided ``tmp_path``.
* **Additive, not rewriting.** Existing test files keep their local
  ``FixtureRunner`` / helpers. This module centralizes the fixture shapes so
  future tests do not re-invent them.
* **No import-time side effects.** Only the standard library and pytest are
  imported at module load. All ``huey.kernel_build.*`` imports happen inside
  the fixtures or the FakeRunner's `run()` method.

Fixture index
-------------
Canonical instances (session-scoped; immutable):

* ``v100_identity``              -- Tesla V100-PCIE-32GB, sm_70, PCI 01:00.0
* ``rx_570_identity``            -- Radeon RX 570, PCI 02:00.0
* ``proprietary_driver_baseline`` -- 580.196.07, proprietary, CUDA API 13.0
* ``source_lock_pinned``         -- a fully pinned ``SourceLock``

Fake runner and results (function-scoped):

* ``fake_runner``     -- a fresh ``FakeRunner`` per test
* ``ok_result``       -- helper returning a zero-exit ``RunnerResult``
* ``fail_result``     -- helper returning a nonzero-exit ``RunnerResult``

Builders (function-scoped callables):

* ``make_kernel_source``  -- a plausible kernel source tree
* ``make_module_tree``    -- a staged ``lib/modules/<kr>/`` tree
* ``make_release_dir``    -- a valid release directory
* ``write_build_yaml``    -- a valid ``kernel/huey-linux/build.yaml``
* ``make_mini_repo``      -- a mini-repo for wrapper tests (Steps 23-26)

Sample data (session-scoped):

* ``nvidia_smi_banner``      -- ``nvidia-smi`` header line with CUDA API
* ``nvidia_smi_one_v100``    -- one-GPU CSV row
* ``nvidia_smi_two_v100``    -- two-GPU CSV rows
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Callable

import pytest


#: Repository root derived from this file's location. Do not touch the
#: filesystem at import time; ``parents[2]`` is pure path arithmetic.
REPO_ROOT = Path(__file__).resolve().parents[2]


# ===========================================================================
# Sample data (bytes, immutable)
# ===========================================================================

#: ``nvidia-smi`` header line as printed by 580.196.07. The "CUDA Version"
#: field is the driver-advertised API, not the installed toolkit.
NVIDIA_SMI_BANNER = (
    b"| NVIDIA-SMI 580.196.07   Driver Version: 580.196.07   "
    b"CUDA Version: 13.0     |\n"
)

#: One V100 CSV row: name, uuid, pci.bus_id, compute_cap.
NVIDIA_SMI_ONE_V100 = (
    b"Tesla V100-PCIE-32GB, GPU-11111111-1111-1111-1111-111111111111, "
    b"00000000:01:00.0, 7.0\n"
)

#: Two V100 rows (the second has a different PCI address and UUID).
NVIDIA_SMI_TWO_V100 = NVIDIA_SMI_ONE_V100 + (
    b"Tesla V100-PCIE-32GB, GPU-22222222-2222-2222-2222-222222222222, "
    b"00000000:02:00.0, 7.0\n"
)


@pytest.fixture(scope="session")
def nvidia_smi_banner() -> bytes:
    return NVIDIA_SMI_BANNER


@pytest.fixture(scope="session")
def nvidia_smi_one_v100() -> bytes:
    return NVIDIA_SMI_ONE_V100


@pytest.fixture(scope="session")
def nvidia_smi_two_v100() -> bytes:
    return NVIDIA_SMI_TWO_V100


# ===========================================================================
# FakeRunner
# ===========================================================================


class FakeRunner:
    """Deterministic :class:`huey.kernel_build.runner.RunnerProtocol` for tests.

    Fail-closed by default: any ``run()`` whose argv does not match a
    registered handler raises :class:`RunnerError`, so an unexpected
    subprocess attempt in a test is loudly reported instead of silently
    no-op'ing.

    Handlers receive only the ``CommandSpec``; the ``dry_run`` and
    ``strict_output`` keyword arguments to ``run()`` are accepted for
    signature compatibility with the real ``Runner`` but are not forwarded
    (tests that need to observe dry-run state can inspect
    :attr:`call_records`).

    Registered handlers are matched in the order they were added. The first
    match wins, so more specific matchers should be registered before more
    general ones. ``on_argv`` and ``on_first_arg`` are convenience wrappers
    around ``on``.
    """

    def __init__(self) -> None:
        self._handlers: list[tuple[Callable, Callable]] = []
        self._records: list[tuple["CommandSpec", bool]] = []  # type: ignore[name-defined]

    def on(self, matcher: Callable, handler: Callable) -> "FakeRunner":
        """Register a handler; ``matcher(spec) -> bool``."""
        self._handlers.append((matcher, handler))
        return self

    def on_argv(self, prefix: tuple[str, ...], handler: Callable) -> "FakeRunner":
        """Register a handler that fires when ``spec.argv`` starts with ``prefix``."""
        n = len(prefix)

        def _matches(spec) -> bool:
            return tuple(spec.argv[:n]) == tuple(prefix)

        return self.on(_matches, handler)

    def on_first_arg(self, first: str, handler: Callable) -> "FakeRunner":
        """Register a handler that fires when ``spec.argv[0] == first``."""

        def _matches(spec) -> bool:
            return bool(spec.argv) and spec.argv[0] == first

        return self.on(_matches, handler)

    def run(self, spec, *, dry_run: bool = False, strict_output: bool = False):  # noqa: ARG002
        self._records.append((spec, dry_run))
        for matcher, handler in self._handlers:
            if matcher(spec):
                return handler(spec)
        # Lazy import so conftest stays importable without the framework.
        from huey.kernel_build.runner import RunnerError

        raise RunnerError(
            f"FakeRunner: no handler for argv={spec.argv!r}. Register one "
            "with .on(), .on_argv(), or .on_first_arg()."
        )

    @property
    def calls(self) -> tuple["CommandSpec", ...]:  # type: ignore[name-defined]
        """The ``CommandSpec`` objects passed to ``run()``, in order."""
        return tuple(spec for spec, _ in self._records)

    @property
    def call_records(self) -> tuple[tuple["CommandSpec", bool], ...]:  # type: ignore[name-defined]
        """The ``(CommandSpec, dry_run)`` pairs passed to ``run()``, in order."""
        return tuple(self._records)


@pytest.fixture
def fake_runner() -> FakeRunner:
    """A fresh empty :class:`FakeRunner` for this test."""
    return FakeRunner()


# ===========================================================================
# Result helpers
# ===========================================================================


def _ok_result(spec, *, stdout: bytes = b"", stderr: bytes = b""):
    from huey.kernel_build.models import CommandResult
    from huey.kernel_build.runner import RunnerResult

    return RunnerResult(
        command=CommandResult(
            argv=spec.argv,
            cwd=str(spec.cwd),
            returncode=0,
            elapsed_seconds=0.0,
        ),
        executed=True,
        dry_run=False,
        stdout=stdout,
        stderr=stderr,
    )


def _fail_result(
    spec, *, returncode: int = 1, stdout: bytes = b"", stderr: bytes = b""
):
    from huey.kernel_build.models import CommandResult
    from huey.kernel_build.runner import RunnerResult

    return RunnerResult(
        command=CommandResult(
            argv=spec.argv,
            cwd=str(spec.cwd),
            returncode=returncode,
            elapsed_seconds=0.0,
        ),
        executed=True,
        dry_run=False,
        stdout=stdout,
        stderr=stderr,
    )


@pytest.fixture
def ok_result() -> Callable[..., object]:
    """Return a factory that produces a zero-exit ``RunnerResult``."""
    return _ok_result


@pytest.fixture
def fail_result() -> Callable[..., object]:
    """Return a factory that produces a nonzero-exit ``RunnerResult``."""
    return _fail_result


# ===========================================================================
# Builders
# ===========================================================================


@pytest.fixture
def make_kernel_source() -> Callable[[Path], Path]:
    """Return a builder for a plausible kernel source tree.

    The tree contains ``Makefile``, ``scripts/kconfig/merge_config.sh``, and
    ``include/generated/`` — the minimum steps 11 and 12 require.
    """

    def build(root: Path) -> Path:
        src = root / "linux-source-7.2.15"
        (src / "scripts" / "kconfig").mkdir(parents=True, exist_ok=True)
        (src / "include" / "generated").mkdir(parents=True, exist_ok=True)
        (src / "Makefile").write_text("# fake kernel Makefile\n", encoding="utf-8")
        merge = src / "scripts" / "kconfig" / "merge_config.sh"
        merge.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        merge.chmod(0o755)
        return src

    return build


@pytest.fixture
def make_module_tree() -> Callable[..., Path]:
    """Return a builder for a staged ``lib/modules/<kr>/`` tree.

    Includes an ``amdgpu.ko`` entry to model the RX 570 display path, plus
    the requested NVIDIA modules (``nvidia`` and ``nvidia-uvm`` by default)
    under ``updates/nvidia/``. ``modules.dep`` is written empty; tests that
    need real dependency data can overwrite it.
    """

    def build(
        root: Path,
        kernel_release: str,
        modules: tuple[str, ...] = ("nvidia", "nvidia-uvm"),
    ) -> Path:
        tree = root / f"modules-{kernel_release}"
        (tree / "kernel" / "drivers" / "gpu" / "drm" / "amd" / "amdgpu").mkdir(
            parents=True, exist_ok=True
        )
        (tree / "kernel" / "drivers" / "gpu" / "drm" / "amd" / "amdgpu" / "amdgpu.ko").write_bytes(
            b"fake amdgpu.ko\n"
        )
        (tree / "updates" / "nvidia").mkdir(parents=True, exist_ok=True)
        for mod in modules:
            (tree / "updates" / "nvidia" / f"{mod}.ko").write_bytes(
                f"fake {mod}.ko\n".encode()
            )
        (tree / "modules.dep").write_text("", encoding="utf-8")
        return tree

    return build


@pytest.fixture
def make_release_dir() -> Callable[..., Path]:
    """Return a builder for a release directory.

    Contains a kernel image ``.deb``, a headers ``.deb``, an ``nvidia-*``
    subdirectory with the requested modules, and an initramfs. Files are
    small text so the release assembler's SHA-256 computation is fast.
    """

    def build(
        root: Path,
        kernel_release: str = "7.2.15-huey1",
        driver_version: str = "580.196.07",
        modules: tuple[str, ...] = ("nvidia", "nvidia-uvm"),
    ) -> Path:
        rd = root / "release"
        rd.mkdir(parents=True, exist_ok=True)
        (rd / f"linux-image-{kernel_release}_7.2.15-huey1-1_amd64.deb").write_bytes(
            b"fake image deb\n"
        )
        (rd / f"linux-headers-{kernel_release}_7.2.15-huey1-1_amd64.deb").write_bytes(
            b"fake headers deb\n"
        )
        nv = rd / f"nvidia-{driver_version}-{kernel_release}"
        nv.mkdir(exist_ok=True)
        for mod in modules:
            (nv / f"{mod}.ko").write_bytes(f"fake {mod}.ko\n".encode())
        (rd / f"initramfs-{kernel_release}").write_bytes(b"fake initramfs\n")
        return rd

    return build


@pytest.fixture
def write_build_yaml() -> Callable[..., Path]:
    """Return a builder for a valid ``kernel/huey-linux/build.yaml``.

    Keyword overrides map to the YAML's fields; unknown keys are ignored so
    a test can pass only the fields it wants to change.
    """

    def build(path: Path, **overrides) -> Path:
        fields: dict[str, object] = {
            "schema_version": 1,
            "profile": "v100-workstation",
            "source_type": "debian-linux-source",
            "source": "linux-source-7.2",
            "version": "7.2.15-1",
            "checksum": "b" * 64,
            "localversion": "-huey1",
            "nvidia_version": "580.196.07",
            "nvidia_module_flavor": "proprietary",
            "jobs": 4,
            "workspace": "build/huey-kernel/workspace",
            "output": "build/huey-kernel/",
            "signing_required_policy": "required_if_secureboot",
        }
        fields.update(overrides)
        text = (
            f"schema_version: {fields['schema_version']}\n"
            f"profile: {fields['profile']}\n"
            "kernel:\n"
            f"  source_type: {fields['source_type']}\n"
            f"  source: {fields['source']}\n"
            f"  version: {fields['version']}\n"
            f"  checksum: '{fields['checksum']}'\n"
            f"  localversion: {fields['localversion']}\n"
            "nvidia:\n"
            f"  version: '{fields['nvidia_version']}'\n"
            f"  module_flavor: {fields['nvidia_module_flavor']}\n"
            "build:\n"
            f"  jobs: {fields['jobs']}\n"
            "paths:\n"
            f"  workspace: {fields['workspace']}\n"
            f"  output: {fields['output']}\n"
            "signing:\n"
            f"  required_policy: {fields['signing_required_policy']}\n"
            "safety:\n"
            "  allow_host_mutation: false\n"
            "  allow_root_build: false\n"
            "  allow_network_fetch: false\n"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    return build


@pytest.fixture
def make_mini_repo() -> Callable[..., Path]:
    """Return a builder for a mini-repo used by wrapper tests (Steps 23-26).

    Copies the named wrapper from the real repository into a ``tmp_path``
    tree and creates an empty ``src/huey`` skeleton. Tests can call
    :meth:`Path.write_text` on ``<repo>/src/huey/kernel_build/cli.py`` to
    install a fake CLI.
    """

    def build(
        root: Path,
        wrapper_name: str,
        *,
        with_src: bool = True,
    ) -> Path:
        repo = root / "mini-repo"
        (repo / "scripts" / "kernel").mkdir(parents=True)
        real = REPO_ROOT / "scripts" / "kernel" / wrapper_name
        if real.is_file():
            dst = repo / "scripts" / "kernel" / wrapper_name
            shutil.copy2(real, dst)
            dst.chmod(0o755)
        if with_src:
            (repo / "src" / "huey" / "kernel_build").mkdir(parents=True)
            (repo / "src" / "huey" / "__init__.py").write_text("", encoding="utf-8")
            (repo / "src" / "huey" / "kernel_build" / "__init__.py").write_text(
                "", encoding="utf-8"
            )
        return repo

    return build


# ===========================================================================
# Canonical instances (immutable, session-scoped)
# ===========================================================================


@pytest.fixture(scope="session")
def v100_identity():
    """Tesla V100-PCIE-32GB, sm_70, at PCI 00000000:01:00.0."""
    from huey.kernel_build.models import GPUIdentity, GPUVendor

    return GPUIdentity(
        vendor=GPUVendor.NVIDIA,
        model="Tesla V100-PCIE-32GB",
        pci_address="00000000:01:00.0",
        uuid="GPU-11111111-1111-1111-1111-111111111111",
        compute_capability="sm_70",
    )


@pytest.fixture(scope="session")
def rx_570_identity():
    """Radeon RX 570 at PCI 00000000:02:00.0 (the display GPU)."""
    from huey.kernel_build.models import GPUIdentity, GPUVendor

    return GPUIdentity(
        vendor=GPUVendor.AMD,
        model="Radeon RX 570",
        pci_address="00000000:02:00.0",
    )


@pytest.fixture(scope="session")
def proprietary_driver_baseline():
    """NVIDIA 580.196.07, proprietary, CUDA API 13.0, toolkit 12.9."""
    from huey.kernel_build.models import DriverBaseline, ModuleFlavor

    return DriverBaseline(
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        cuda_api_version="13.0",
        cuda_toolkit_version="12.9",
        dkms_builds=("7.2.12+deb14-amd64", "7.2.15+deb14-amd64"),
    )


@pytest.fixture(scope="session")
def source_lock_pinned():
    """A fully pinned source lock for ``linux-source-7.2`` 7.2.15-1."""
    from huey.kernel_build.models import SourceType
    from huey.kernel_build.source_manager import SourceLock

    return SourceLock(
        schema_version=1,
        status="pinned",
        source_type=SourceType.DEBIAN_LINUX_SOURCE,
        package_name="linux-source-7.2",
        version="7.2.15-1",
        archive_filename="linux-source-7.2_7.2.15-1_all.deb",
        origin_url=(
            "https://deb.debian.org/debian/pool/main/l/linux/"
            "linux-source-7.2_7.2.15-1_all.deb"
        ),
        checksum_sha256="b" * 64,
        retrieved_date="2026-11-12",
        license="GPL-2.0-only",
        profile_revision=1,
        notes="fixture for tests/kernel_build",
    )


# ===========================================================================
# Sanity: no host paths at import time
# ===========================================================================

_ = hashlib  # keep the import for future fixture use; avoids unused-import warnings
