"""Guard for kernel/huey-linux/profiles/v100-workstation.config (Step 10).

These tests do not run ``merge_config.sh`` or ``make olddefconfig``; that
integration is exercised in Step 11 (``test_config_builder.py``). This file
guards the checked-in fragment itself: the specific symbols that must be set
or must not be set, and the absence of accidental drift into unrelated
subsystems.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAGMENT = REPO_ROOT / "kernel" / "huey-linux" / "profiles" / "v100-workstation.config"

_LINE_RE = re.compile(r"^\s*(CONFIG_[A-Z0-9_]+)=(.*?)\s*$")
_UNSET_RE = re.compile(r"^\s*#\s*(CONFIG_[A-Z0-9_]+) is not set\s*$")


def _read() -> str:
    assert FRAGMENT.is_file(), f"missing {FRAGMENT}"
    return FRAGMENT.read_text(encoding="utf-8")


def _assigned() -> dict[str, str]:
    result: dict[str, str] = {}
    for line in _read().splitlines():
        m = _LINE_RE.match(line)
        if m:
            result[m.group(1)] = m.group(2)
    return result


def _unset() -> set[str]:
    result: set[str] = set()
    for line in _read().splitlines():
        m = _UNSET_RE.match(line)
        if m:
            result.add(m.group(1))
    return result


# ---------------------------------------------------------------------------
# File shape
# ---------------------------------------------------------------------------


def test_fragment_exists_and_is_nonempty() -> None:
    assert _read().strip()


def test_fragment_is_not_a_complete_dot_config() -> None:
    """A fragment must be small; a complete .config would be thousands of lines."""
    line_count = len(_read().splitlines())
    assert line_count < 120, (
        f"fragment has {line_count} lines; it looks like a complete .config. "
        "Only intentional deltas belong here."
    )


# ---------------------------------------------------------------------------
# Nouveau: must be explicitly unset
# ---------------------------------------------------------------------------


def test_nouveau_is_explicitly_unset() -> None:
    """Nouveau must not be enabled: it would claim the Tesla V100."""
    assert "CONFIG_DRM_NOUVEAU" in _unset(), (
        "v100-workstation.config must contain '# CONFIG_DRM_NOUVEAU is not set'. "
        "If Nouveau binds the V100, the proprietary nvidia module cannot "
        "initialize the GPU."
    )


def test_nouveau_is_not_assigned_y_or_m() -> None:
    assigned = _assigned()
    assert "CONFIG_DRM_NOUVEAU" not in assigned, (
        "CONFIG_DRM_NOUVEAU must be expressed as '# ... is not set', not "
        "assigned =y or =m."
    )


def test_lab_config_nouveau_conflict_is_documented() -> None:
    """The fragment must explain why it overrides lab.config's Nouveau=y."""
    text = _read().lower()
    assert "lab.config" in text, (
        "The fragment must mention src/huey/core/lab.config so a future reader "
        "understands why CONFIG_DRM_NOUVEAU=y from that file is overridden."
    )
    assert "nouveau" in text


# ---------------------------------------------------------------------------
# AMDGPU: must remain a module
# ---------------------------------------------------------------------------


def test_amdgpu_is_module() -> None:
    assigned = _assigned()
    assert assigned.get("CONFIG_DRM_AMDGPU") == "m", (
        "CONFIG_DRM_AMDGPU must be 'm'. Forcing '=y' can drag firmware into "
        "the kernel image or the initramfs for the RX 570 display path, which "
        "is not the intent of this profile."
    )


def test_amdgpu_is_not_built_in() -> None:
    assigned = _assigned()
    assert assigned.get("CONFIG_DRM_AMDGPU") != "y", (
        "CONFIG_DRM_AMDGPU=y is not allowed in this fragment; build it as a "
        "module unless a separately reviewed change is made."
    )


# ---------------------------------------------------------------------------
# External module support
# ---------------------------------------------------------------------------


def test_modules_enabled() -> None:
    assert _assigned().get("CONFIG_MODULES") == "y", (
        "CONFIG_MODULES=y is required; otherwise no out-of-tree modules can "
        "load, including the proprietary NVIDIA driver."
    )


def test_modversions_enabled() -> None:
    assert _assigned().get("CONFIG_MODVERSIONS") == "y", (
        "CONFIG_MODVERSIONS=y is required for the proprietary NVIDIA external "
        "module build (the kernel must be fully built to produce "
        "Module.symvers CRCs)."
    )


# ---------------------------------------------------------------------------
# Guard: no accidental drift into unrelated subsystems
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden_symbol",
    [
        "CONFIG_EXT4_FS",
        "CONFIG_BTRFS_FS",
        "CONFIG_NVME_CORE",
        "CONFIG_BLK_DEV_NVME",
        "CONFIG_SATA_AHCI",
        "CONFIG_PCI",
        "CONFIG_PCI_MSI",
        "CONFIG_INTEL_IOMMU",
        "CONFIG_IOMMU_SUPPORT",
        "CONFIG_USB_SUPPORT",
        "CONFIG_USB_XHCI_HCD",
        "CONFIG_E1000E",
        "CONFIG_IGC",
        "CONFIG_DRM_I915",
    ],
)
def test_unrelated_subsystems_not_assigned(forbidden_symbol: str) -> None:
    """Boot-critical and unrelated symbols must not be overridden here."""
    assigned = _assigned()
    unset = _unset()
    assert forbidden_symbol not in assigned, (
        f"{forbidden_symbol} must not be set in this fragment; it is inherited "
        "from the Debian base config. Changes require a separately reviewed "
        "fragment."
    )
    assert forbidden_symbol not in unset, (
        f"{forbidden_symbol} must not be unset in this fragment."
    )


# ---------------------------------------------------------------------------
# Comment hygiene
# ---------------------------------------------------------------------------


def test_each_assignment_has_a_preceding_comment() -> None:
    """Intentional deltas must be justified in a comment above them."""
    lines = _read().splitlines()
    missing: list[str] = []
    for idx, line in enumerate(lines):
        m = _LINE_RE.match(line)
        if not m:
            continue
        # Look backwards for the nearest non-empty line; require a comment.
        j = idx - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        if j < 0 or not lines[j].lstrip().startswith("#"):
            missing.append(m.group(1))
    assert not missing, (
        f"Assignments without a preceding comment: {missing}. Every intentional "
        "delta must document why it exists."
    )
