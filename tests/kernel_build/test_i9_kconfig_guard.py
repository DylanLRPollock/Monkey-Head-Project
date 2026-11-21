"""Offline tests for the standalone 7.3.4 i9 Kconfig safety gate."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "kernel" / "validate_i9_kconfig.py"
SPEC = importlib.util.spec_from_file_location("validate_i9_kconfig", SCRIPT)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)

_BASE = """
CONFIG_X86_64=y
CONFIG_PCI=y
CONFIG_EFI=y
CONFIG_EFI_STUB=y
CONFIG_EFI_PARTITION=y
CONFIG_MODULES=y
CONFIG_VMD=m
CONFIG_NVME_CORE=m
CONFIG_BLK_DEV_NVME=m
CONFIG_BLK_DEV_MD=m
CONFIG_MD_RAID10=m
CONFIG_BTRFS_FS=m
CONFIG_SATA_AHCI=m
CONFIG_MD_RAID0=m
CONFIG_MD_RAID1=m
CONFIG_FAT_FS=m
CONFIG_VFAT_FS=m
CONFIG_LOCALVERSION=""
# CONFIG_LOCALVERSION_AUTO is not set
# CONFIG_MODVERSIONS is not set
CONFIG_DRM_I915=m
CONFIG_DRM_AMDGPU=m
# CONFIG_DRM_NOUVEAU is not set
"""


def test_complete_staged_testing1_passes() -> None:
    result = guard.check_config(_BASE, "testing1")
    assert result["ok"], result
    assert not result["errors"]


def test_running_debian_nouveau_is_warning() -> None:
    original = _BASE.replace(
        "# CONFIG_DRM_NOUVEAU is not set", "CONFIG_DRM_NOUVEAU=m"
    )
    result = guard.check_config(original, "baseline")
    assert result["ok"], result
    assert any("NOUVEAU" in finding for finding in result["warnings"])


@pytest.mark.parametrize(
    "symbol",
    ("CONFIG_VMD", "CONFIG_BLK_DEV_NVME", "CONFIG_MD_RAID10",
     "CONFIG_BTRFS_FS", "CONFIG_SATA_AHCI", "CONFIG_MD_RAID0",
     "CONFIG_MD_RAID1"),
)
def test_critical_boot_driver_missing_blocks(symbol: str) -> None:
    result = guard.check_config(_BASE.replace(f"{symbol}=m\n", ""), "testing1")
    assert not result["ok"]
    assert any(symbol in finding for finding in result["errors"])


def test_candidate_nouveau_blocks_build() -> None:
    cfg = _BASE.replace(
        "# CONFIG_DRM_NOUVEAU is not set", "CONFIG_DRM_NOUVEAU=m"
    )
    result = guard.check_config(cfg, "testing1")
    assert not result["ok"]


def test_intel_only_can_omit_amdgpu() -> None:
    cfg = _BASE.replace(
        "CONFIG_DRM_AMDGPU=m", "# CONFIG_DRM_AMDGPU is not set"
    )
    assert guard.check_config(cfg, "intel-only")["ok"]
    assert not guard.check_config(cfg, "testing1")["ok"]


def test_duplicate_kconfig_symbol_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        guard.parse_config(_BASE + "CONFIG_X86_64=y\n")


def test_unexpected_embedded_localversion_is_rejected() -> None:
    cfg = _BASE.replace('CONFIG_LOCALVERSION=""', 'CONFIG_LOCALVERSION="-extra"')
    assert not guard.check_config(cfg, "testing1")["ok"]


def test_modversions_y_warns_for_first_candidate() -> None:
    cfg = _BASE.replace(
        "# CONFIG_MODVERSIONS is not set", "CONFIG_MODVERSIONS=y"
    )
    result = guard.check_config(cfg, "testing1")
    assert result["ok"]
    assert any("MODVERSIONS" in finding for finding in result["warnings"])
