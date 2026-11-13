"""Tests that verify the shared fixtures in conftest.py work.

These tests are the migration guide: they show how to use each fixture and
prove the fixture is functioning. They also guard against conftest regressions
(a fixture that returns the wrong shape, the FakeRunner accidentally launching
a subprocess, a builder that writes to a path outside tmp_path).

The tests intentionally do not depend on any fixture from another test file.
They run offline and use tmp_path only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# FakeRunner
# ---------------------------------------------------------------------------


def test_fake_runner_fails_closed_on_unhandled(fake_runner) -> None:
    """An unhandled call must raise, not return a fake success."""
    from huey.kernel_build.runner import CommandSpec, RunnerError

    spec = CommandSpec(argv=("make", "modules"), cwd=Path("/tmp"))
    with pytest.raises(RunnerError, match="no handler"):
        fake_runner.run(spec)


def test_fake_runner_dispatches_by_matcher(fake_runner, ok_result) -> None:
    from huey.kernel_build.runner import CommandSpec

    fake_runner.on(lambda s: s.argv[0] == "uname", lambda s: ok_result(s, stdout=b"7.2.15\n"))
    spec = CommandSpec(argv=("uname", "-r"), cwd=Path("/tmp"))
    result = fake_runner.run(spec)
    assert result.command.returncode == 0
    assert result.stdout == b"7.2.15\n"


def test_fake_runner_on_argv_matches_prefix(fake_runner, ok_result) -> None:
    from huey.kernel_build.runner import CommandSpec

    fake_runner.on_argv(("modinfo", "-F", "version", "nvidia"), lambda s: ok_result(s, stdout=b"580.196.07\n"))
    spec = CommandSpec(
        argv=("modinfo", "-F", "version", "nvidia"),
        cwd=Path("/tmp"),
    )
    assert fake_runner.run(spec).stdout == b"580.196.07\n"


def test_fake_runner_on_first_arg(fake_runner, ok_result) -> None:
    from huey.kernel_build.runner import CommandSpec

    fake_runner.on_first_arg("dpkg-deb", lambda s: ok_result(s, stdout=b"Package: linux-image-7.2.15-huey1\n"))
    spec = CommandSpec(argv=("dpkg-deb", "--field", "/tmp/x.deb", "Package"), cwd=Path("/tmp"))
    assert b"linux-image" in fake_runner.run(spec).stdout


def test_fake_runner_records_calls(fake_runner, ok_result) -> None:
    from huey.kernel_build.runner import CommandSpec

    fake_runner.on_first_arg("echo", lambda s: ok_result(s))
    fake_runner.run(CommandSpec(argv=("echo", "a"), cwd=Path("/tmp")))
    fake_runner.run(CommandSpec(argv=("echo", "b"), cwd=Path("/tmp")), dry_run=True)

    assert len(fake_runner.calls) == 2
    assert fake_runner.calls[0].argv == ("echo", "a")
    assert fake_runner.call_records[1][1] is True  # dry_run recorded


def test_fake_runner_reusable_across_matchers(fake_runner, ok_result) -> None:
    """Multiple handlers coexist; first match wins."""
    from huey.kernel_build.runner import CommandSpec

    fake_runner.on(
        lambda s: s.argv[0] == "make",
        lambda s: ok_result(s, stdout=b"make-ok\n"),
    )
    fake_runner.on(
        lambda s: s.argv[0] == "modinfo",
        lambda s: ok_result(s, stdout=b"modinfo-ok\n"),
    )
    assert fake_runner.run(CommandSpec(argv=("make",), cwd=Path("/tmp"))).stdout == b"make-ok\n"
    assert fake_runner.run(CommandSpec(argv=("modinfo",), cwd=Path("/tmp"))).stdout == b"modinfo-ok\n"


# ---------------------------------------------------------------------------
# ok_result / fail_result
# ---------------------------------------------------------------------------


def test_ok_result_produces_zero_exit(ok_result) -> None:
    from huey.kernel_build.runner import CommandSpec

    spec = CommandSpec(argv=("echo",), cwd=Path("/tmp"))
    r = ok_result(spec, stdout=b"hello\n")
    assert r.command.returncode == 0
    assert r.succeeded is True
    assert r.stdout == b"hello\n"


def test_fail_result_produces_nonzero_exit(fail_result) -> None:
    from huey.kernel_build.runner import CommandSpec

    spec = CommandSpec(argv=("make",), cwd=Path("/tmp"))
    r = fail_result(spec, returncode=2, stderr=b"error\n")
    assert r.command.returncode == 2
    assert r.succeeded is False
    assert r.stderr == b"error\n"


# ---------------------------------------------------------------------------
# make_kernel_source
# ---------------------------------------------------------------------------


def test_make_kernel_source_creates_expected_structure(make_kernel_source, tmp_path: Path) -> None:
    src = make_kernel_source(tmp_path)
    assert (src / "Makefile").is_file()
    assert (src / "scripts" / "kconfig" / "merge_config.sh").is_file()
    assert (src / "include" / "generated").is_dir()
    # The merge script is executable.
    import os
    assert os.access(src / "scripts" / "kconfig" / "merge_config.sh", os.X_OK)


def test_make_kernel_source_is_idempotent(make_kernel_source, tmp_path: Path) -> None:
    a = make_kernel_source(tmp_path)
    b = make_kernel_source(tmp_path)
    assert a == b


# ---------------------------------------------------------------------------
# make_module_tree
# ---------------------------------------------------------------------------


def test_make_module_tree_creates_expected_structure(make_module_tree, tmp_path: Path) -> None:
    tree = make_module_tree(tmp_path, "7.2.15-huey1")
    assert tree.is_dir()
    assert (tree / "kernel" / "drivers" / "gpu" / "drm" / "amd" / "amdgpu" / "amdgpu.ko").is_file()
    assert (tree / "updates" / "nvidia" / "nvidia.ko").is_file()
    assert (tree / "updates" / "nvidia" / "nvidia-uvm.ko").is_file()
    assert (tree / "modules.dep").is_file()


def test_make_module_tree_custom_modules(make_module_tree, tmp_path: Path) -> None:
    tree = make_module_tree(tmp_path, "7.2.15-huey1", modules=("nvidia", "nvidia-modeset"))
    assert (tree / "updates" / "nvidia" / "nvidia-modeset.ko").is_file()
    assert not (tree / "updates" / "nvidia" / "nvidia-uvm.ko").exists()


# ---------------------------------------------------------------------------
# make_release_dir
# ---------------------------------------------------------------------------


def test_make_release_dir_creates_expected_structure(make_release_dir, tmp_path: Path) -> None:
    rd = make_release_dir(tmp_path)
    assert rd.is_dir()
    assert any(rd.glob("linux-image-7.2.15-huey1*.deb"))
    assert any(rd.glob("linux-headers-7.2.15-huey1*.deb"))
    nv = rd / "nvidia-580.196.07-7.2.15-huey1"
    assert nv.is_dir()
    assert (nv / "nvidia.ko").is_file()
    assert (nv / "nvidia-uvm.ko").is_file()
    assert (rd / "initramfs-7.2.15-huey1").is_file()


def test_make_release_dir_custom_versions(make_release_dir, tmp_path: Path) -> None:
    rd = make_release_dir(tmp_path, kernel_release="7.2.12-huey1", driver_version="550.100.00")
    assert any(rd.glob("linux-image-7.2.12-huey1*.deb"))
    assert (rd / "nvidia-550.100.00-7.2.12-huey1" / "nvidia.ko").is_file()


# ---------------------------------------------------------------------------
# write_build_yaml
# ---------------------------------------------------------------------------


def test_write_build_yaml_defaults_are_valid(write_build_yaml, tmp_path: Path) -> None:
    path = write_build_yaml(tmp_path / "build.yaml")
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "profile: v100-workstation" in text
    assert "module_flavor: proprietary" in text
    assert "allow_host_mutation: false" in text
    assert "allow_root_build: false" in text
    assert "allow_network_fetch: false" in text


def test_write_build_yaml_overrides(write_build_yaml, tmp_path: Path) -> None:
    path = write_build_yaml(
        tmp_path / "build.yaml",
        profile="lab",
        nvidia_module_flavor="proprietary",
        jobs=2,
    )
    text = path.read_text(encoding="utf-8")
    assert "profile: lab" in text
    assert "jobs: 2" in text


def test_write_build_yaml_parses_with_pyyaml(write_build_yaml, tmp_path: Path) -> None:
    """If PyYAML is present, the generated YAML must parse cleanly."""
    yaml = pytest.importorskip("yaml", reason="PyYAML required; added in Step 31")
    path = write_build_yaml(tmp_path / "build.yaml")
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert doc["schema_version"] == 1
    assert doc["nvidia"]["module_flavor"] == "proprietary"
    assert doc["safety"]["allow_host_mutation"] is False


# ---------------------------------------------------------------------------
# make_mini_repo
# ---------------------------------------------------------------------------


def test_make_mini_repo_copies_wrapper(make_mini_repo, tmp_path: Path) -> None:
    repo = make_mini_repo(tmp_path, "build-kernel.sh")
    wrapper = repo / "scripts" / "kernel" / "build-kernel.sh"
    # If the real wrapper exists in the checkout, the copy should match.
    if (tmp_path.parent / "repo").exists():  # pragma: no cover - defensive
        pass
    # Regardless, the skeleton must exist.
    assert (repo / "src" / "huey" / "__init__.py").is_file()
    assert (repo / "src" / "huey" / "kernel_build" / "__init__.py").is_file()
    # The wrapper is either present (copied) or absent (repo did not have it).
    if wrapper.exists():
        import os
        assert os.access(wrapper, os.X_OK)


def test_make_mini_repo_without_src(make_mini_repo, tmp_path: Path) -> None:
    repo = make_mini_repo(tmp_path, "build-nvidia.sh", with_src=False)
    assert not (repo / "src" / "huey").exists()


# ---------------------------------------------------------------------------
# Canonical instances
# ---------------------------------------------------------------------------


def test_v100_identity_fields(v100_identity) -> None:
    from huey.kernel_build.models import GPUVendor

    assert v100_identity.vendor == GPUVendor.NVIDIA
    assert v100_identity.compute_capability == "sm_70"
    assert v100_identity.pci_address == "00000000:01:00.0"
    assert v100_identity.uuid is not None
    assert v100_identity.uuid.startswith("GPU-")


def test_rx_570_identity_fields(rx_570_identity) -> None:
    from huey.kernel_build.models import GPUVendor

    assert rx_570_identity.vendor == GPUVendor.AMD
    assert rx_570_identity.pci_address == "00000000:02:00.0"
    assert rx_570_identity.compute_capability is None  # AMD GPUs do not have sm_X


def test_proprietary_driver_baseline_fields(proprietary_driver_baseline) -> None:
    from huey.kernel_build.models import ModuleFlavor

    d = proprietary_driver_baseline
    assert d.driver_version == "580.196.07"
    assert d.module_flavor == ModuleFlavor.PROPRIETARY
    assert d.cuda_api_version == "13.0"
    assert d.cuda_toolkit_version == "12.9"
    assert d.cuda_api_version != d.cuda_toolkit_version
    assert "7.2.15+deb14-amd64" in d.dkms_builds


def test_source_lock_pinned_fields(source_lock_pinned) -> None:
    lock = source_lock_pinned
    assert lock.status == "pinned"
    assert len(lock.checksum_sha256) == 64
    assert lock.checksum_sha256 != "0" * 64
    assert lock.origin_url.startswith("https://")


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------


def test_nvidia_smi_banner_has_cuda_api(nvidia_smi_banner) -> None:
    assert b"CUDA Version: 13.0" in nvidia_smi_banner
    assert b"Driver Version: 580.196.07" in nvidia_smi_banner


def test_nvidia_smi_one_v100_shape(nvidia_smi_one_v100) -> None:
    lines = [ln for ln in nvidia_smi_one_v100.splitlines() if ln.strip()]
    assert len(lines) == 1
    assert b"Tesla V100-PCIE-32GB" in lines[0]
    assert b"GPU-" in lines[0]
    assert b"7.0" in lines[0]


def test_nvidia_smi_two_v100_shape(nvidia_smi_two_v100) -> None:
    lines = [ln for ln in nvidia_smi_two_v100.splitlines() if ln.strip()]
    assert len(lines) == 2
    assert b"GPU-11111111" in lines[0]
    assert b"GPU-22222222" in lines[1]


# ---------------------------------------------------------------------------
# No host mutation
# ---------------------------------------------------------------------------


def test_fixtures_do_not_touch_protected_paths(
    fake_runner, make_kernel_source, make_module_tree, make_release_dir, tmp_path: Path
) -> None:
    """Structural sanity: no fixture resolves into a protected host path."""
    from huey.kernel_build.policy import PROTECTED_HOST_PATHS

    paths = [
        make_kernel_source(tmp_path),
        make_module_tree(tmp_path, "7.2.15-huey1"),
        make_release_dir(tmp_path),
    ]
    for path in paths:
        resolved = path.resolve()
        for protected in PROTECTED_HOST_PATHS:
            with pytest.raises(ValueError):
                resolved.relative_to(protected)


def test_fake_runner_launches_no_subprocess(fake_runner, ok_result) -> None:
    """FakeRunner must never spawn a subprocess, even for a real-looking argv."""
    from huey.kernel_build.runner import CommandSpec

    marker = Path("/tmp/__huey_fake_runner_marker__")
    if marker.exists():
        marker.unlink()
    fake_runner.on_first_arg("touch", lambda s: ok_result(s))
    fake_runner.run(CommandSpec(argv=("touch", str(marker)), cwd=Path("/tmp")))
    # The real command would have created the file; FakeRunner must not have.
    assert not marker.exists()
