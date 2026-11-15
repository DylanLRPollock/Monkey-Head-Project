"""Static safeguards for read-only testing2 kernel-build readiness audit."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/kernel/huey-734-testing2-prebuild-gate.sh"


def _script() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_testing2_candidate_and_signed_source_hashes_pinned() -> None:
    contents = _script()
    assert "b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f" in contents
    assert "db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3" in contents
    assert "1c72bf3f45c2dac5318d80ec373fcb04b8e2a423b005f8a12a6da18e2c614762" in contents
    assert "7.3.4-huey-testing2" in contents


def test_root_drivers_and_gpu_policy_are_verified() -> None:
    contents = _script()
    assert "VMD NVME_CORE BLK_DEV_NVME BLK_DEV_MD MD_RAID10" in contents
    assert "MD_RAID0 MD_RAID1 BTRFS_FS SATA_AHCI DRM_I915 DRM_AMDGPU" in contents
    assert "RUST RUST_IS_AVAILABLE DEBUG_INFO_BTF" in contents
    assert "LOCALVERSION_AUTO MODVERSIONS DRM_NOUVEAU MODULE_SIG_FORCE" in contents


def test_no_privileged_or_install_actions() -> None:
    for line in _script().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert not any(
            line.startswith(cmd)
            for cmd in ("sudo ", "apt ", "dpkg -i", "update-grub",
                        "update-initramfs", "grub-install", "reboot",
                        "poweroff", "modprobe", "mdadm --", "make ")
        )


def test_module_signing_is_explicit_not_silent() -> None:
    contents = _script()
    assert 'CONFIG_MODULE_SIG_ALL=y' in contents
    assert 'CONFIG_MODULE_SIG_KEY="certs/signing_key.pem"' in contents
    assert "signing" in contents.lower()
