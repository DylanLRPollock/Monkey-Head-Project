#!/usr/bin/env python3
"""Read-only, fail-closed config guard for HueyOS 7.3.4 i9 workstation.

This checks Kconfig symbol availability, not module inclusion in an initramfs.
The required boot modules and mdadm hooks must be verified independently.
It never changes the kernel, filesystem, devices, bootloader, or config.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

_SET = re.compile(r"^(CONFIG_[A-Z0-9_]+)=(.*)$")
_UNSET = re.compile(r"^# (CONFIG_[A-Z0-9_]+) is not set$")

_ALWAYS_ENABLED = {
    "CONFIG_X86_64": ("y",),
    "CONFIG_PCI": ("y",),
    "CONFIG_EFI": ("y",),
    "CONFIG_EFI_STUB": ("y",),
    "CONFIG_EFI_PARTITION": ("y",),
    "CONFIG_MODULES": ("y",),
}
# Built-in=y and modular=m are both acceptable. Modules must be present in
# the initramfs for the Optane + RAID10 root to boot.
_BOOT_DRIVERS = {
    "CONFIG_VMD": ("y", "m"),
    "CONFIG_NVME_CORE": ("y", "m"),
    "CONFIG_BLK_DEV_NVME": ("y", "m"),
    "CONFIG_BLK_DEV_MD": ("y", "m"),
    "CONFIG_MD_RAID10": ("y", "m"),
    "CONFIG_BTRFS_FS": ("y", "m"),
    "CONFIG_SATA_AHCI": ("y", "m"),
    "CONFIG_MD_RAID0": ("y", "m"),
    "CONFIG_MD_RAID1": ("y", "m"),
    "CONFIG_FAT_FS": ("y", "m"),
    "CONFIG_VFAT_FS": ("y", "m"),
}
_USEFUL = (
    "CONFIG_IGC", "CONFIG_IWLWIFI", "CONFIG_CPU_FREQ",
    "CONFIG_X86_INTEL_PSTATE", "CONFIG_INTEL_IDLE",
    "CONFIG_DEBUG_INFO_BTF", "CONFIG_DRM_XE", "CONFIG_RUST",
)


def parse_config(text: str) -> dict[str, str]:
    config: dict[str, str] = {}
    for line in text.splitlines():
        m = _SET.match(line) or _UNSET.match(line)
        if m:
            value = m.group(2) if m.re is _SET else "n"
            if m.group(1) in config:
                raise ValueError(f"duplicate Kconfig symbol {m.group(1)}")
            config[m.group(1)] = value
    if not config:
        raise ValueError("no Kconfig symbols found")
    return config


def check_config(text: str, stage: str = "baseline") -> dict:
    if stage not in {"baseline", "testing1", "intel-only"}:
        raise ValueError("unsupported stage")
    c = parse_config(text)
    errors: list[str] = []
    warnings: list[str] = []
    for name, accepted in {**_ALWAYS_ENABLED, **_BOOT_DRIVERS}.items():
        if c.get(name, "n") not in accepted:
            expected = "/".join(accepted)
            errors.append(
                f"{name}={c.get(name, 'not found')} (must be {expected})"
            )

    if c.get("CONFIG_LOCALVERSION") != '""':
        errors.append(
            "CONFIG_LOCALVERSION must be empty; use one build LOCALVERSION suffix"
        )
    if c.get("CONFIG_LOCALVERSION_AUTO", "n") != "n":
        errors.append("CONFIG_LOCALVERSION_AUTO must be disabled")
    if c.get("CONFIG_MODVERSIONS", "n") != "n":
        warnings.append(
            "CONFIG_MODVERSIONS differs from tested Debian baseline (n): "
            "requalify R580 modules"
        )

    if c.get("CONFIG_DRM_I915", "n") not in {"m", "y"}:
        errors.append("CONFIG_DRM_I915 must support Intel UHD 770")
    if stage in {"baseline", "testing1"} and c.get("CONFIG_DRM_AMDGPU", "n") != "m":
        errors.append(
            "Initial testing1/baseline must retain AMDGPU=m as display fallback"
        )
    if c.get("CONFIG_DRM_NOUVEAU", "n") != "n":
        msg = "CONFIG_DRM_NOUVEAU must be disabled for proprietary V100 profile"
        (warnings if stage == "baseline" else errors).append(msg)

    for name in _USEFUL:
        if c.get(name, "n") == "n":
            warnings.append(f"{name} is disabled or absent; review before deployment")

    info = {
        "stage": stage,
        "symbols_seen": len(c),
        "intel_i915": c.get("CONFIG_DRM_I915", "n"),
        "amd_rx570_amdgpu": c.get("CONFIG_DRM_AMDGPU", "n"),
        "nouveau": c.get("CONFIG_DRM_NOUVEAU", "n"),
        "modversions": c.get("CONFIG_MODVERSIONS", "n"),
        "rust": c.get("CONFIG_RUST", "n"),
        "btf": c.get("CONFIG_DEBUG_INFO_BTF", "n"),
        "cc_version": c.get("CONFIG_CC_VERSION_TEXT", ""),
        "preemption": c.get("CONFIG_PREEMPT_DYNAMIC", "n"),
        "hz": c.get("CONFIG_HZ", ""),
    }
    return {"ok": not errors, "errors": errors, "warnings": warnings, "info": info}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="existing complete kernel .config")
    parser.add_argument(
        "--stage", choices=("baseline", "testing1", "intel-only"),
        default="baseline",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    args = parser.parse_args(argv)
    try:
        result = check_config(args.config.read_text(encoding="utf-8"), args.stage)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"HueyOS Kconfig {args.stage}: {'PASS' if result['ok'] else 'FAIL'}")
        print(f"Symbols parsed: {result['info']['symbols_seen']}")
        for key, value in result["info"].items():
            if key != "symbols_seen":
                print(f"  {key}: {value}")
        for e in result["errors"]:
            print(f"[ERROR] {e}")
        for w in result["warnings"]:
            print(f"[WARN] {w}")
    return 0 if result["ok"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
