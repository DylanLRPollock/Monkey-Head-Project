# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Gpu module (src/monkey_head/utils)

"""Hardware accelerator detection utilities for HueyOS and Monkey Head."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

LOGGER = logging.getLogger(__name__)

_AMD_VENDOR_IDS = {"0x1002", "0x1022"}
_NVIDIA_VENDOR_IDS = {"0x10de"}
_INTEL_VENDOR_IDS = {"0x8086"}

_MODEL_TIERS: Sequence[Tuple[int, List[str]]] = (
    (48 * 1024**3, ["deepseek_ollama_r1_70b", "llama3.1:70b"]),
    (32 * 1024**3, ["deepseek_ollama_r1_32b", "llama3.1"]),
    (24 * 1024**3, ["deepseek_ollama_r1_14b", "llama3.1"]),
    (16 * 1024**3, ["deepseek_ollama_r1_7b", "llama3.1"]),
    (8 * 1024**3, ["deepseek_ollama_r1_1.5b", "llama3.1"]),
    (4 * 1024**3, ["deepseek_ollama_r1_1.5b", "llama3.1"]),
    (0, ["llama3.1"]),
)


@dataclass(slots=True)
class AcceleratorInfo:
    """Normalised hardware accelerator metadata."""

    name: str
    vendor: str
    driver: str
    backend: str
    vram_total: Optional[int]
    vram_free: Optional[int]
    bus_id: Optional[str] = None
    node: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "vendor": self.vendor,
            "driver": self.driver,
            "backend": self.backend,
            "vram_total": self.vram_total,
            "vram_free": self.vram_free,
            "bus_id": self.bus_id,
            "node": self.node,
        }


def detect_accelerators(*, sys_root: Optional[Path] = None) -> List[AcceleratorInfo]:
    """Return a list of detected GPUs/accelerators with VRAM metrics."""

    root = sys_root or Path("/sys/class/drm")
    infos = _detect_from_sysfs(root)
    needs_rocm = [info for info in infos if info.backend == "rocm" and info.vram_total is None]
    if needs_rocm:
        rocm_map = _detect_from_rocm_smi()
        for info in needs_rocm:
            candidates = (
                rocm_map.get(info.node or "")
                or rocm_map.get(info.bus_id or "")
                or rocm_map.get(info.name)
            )
            if candidates:
                info.vram_total = candidates.get("total")
                info.vram_free = candidates.get("free")
    return infos


def total_vram_bytes(accelerators: Iterable[AcceleratorInfo]) -> int:
    """Return the total VRAM across detected accelerators."""

    total = 0
    for info in accelerators:
        if info.vram_total:
            total += int(info.vram_total)
    return total


def recommend_models_for_vram(vram_bytes: Optional[int]) -> List[str]:
    """Return recommended local models for the given VRAM capacity."""

    capacity = int(vram_bytes or 0)
    for threshold, models in _MODEL_TIERS:
        if capacity >= threshold:
            return list(models)
    return list(_MODEL_TIERS[-1][1])


def _detect_from_sysfs(root: Path) -> List[AcceleratorInfo]:
    if not root.exists():
        return []

    infos: List[AcceleratorInfo] = []
    for card_dir in sorted(root.glob("card[0-9]*")):
        device_dir = card_dir / "device"
        if not device_dir.exists():
            continue

        vendor_id = _read_text(device_dir / "vendor")
        vendor = _vendor_name(vendor_id)
        driver = _driver_name(device_dir)
        backend = "rocm" if driver == "amdgpu" else "unknown"
        uevent = _parse_key_value(device_dir / "uevent")
        bus_id = uevent.get("PCI_SLOT_NAME")
        name = (
            uevent.get("PRODUCT_NAME")
            or uevent.get("PCI_ID")
            or _read_text(device_dir / "product_name")
            or _read_text(device_dir / "device")
            or card_dir.name
        )
        name = _format_name(name, vendor, bus_id, driver)

        vram_total = _read_int(device_dir / "mem_info_vram_total")
        vram_used = _read_int(device_dir / "mem_info_vram_used")
        if vram_total is None:
            vram_total = _read_int(device_dir / "mem_info_vis_vram_total")
            vram_used = _read_int(device_dir / "mem_info_vis_vram_used")
        vram_free: Optional[int] = None
        if vram_total is not None and vram_used is not None:
            try:
                vram_free = max(int(vram_total) - int(vram_used), 0)
            except (TypeError, ValueError):
                vram_free = None

        infos.append(
            AcceleratorInfo(
                name=name,
                vendor=vendor,
                driver=driver or uevent.get("DRIVER", "unknown"),
                backend=backend,
                vram_total=vram_total,
                vram_free=vram_free,
                bus_id=bus_id,
                node=card_dir.name,
            )
        )
    return infos


def _detect_from_rocm_smi() -> Dict[str, Dict[str, Optional[int]]]:
    rocm_smi = shutil.which("rocm-smi")
    if not rocm_smi:
        return {}
    try:
        output = subprocess.check_output(
            [rocm_smi, "--showmeminfo", "vram", "--json"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
    except Exception:  # pragma: no cover - depends on runtime environment
        LOGGER.debug("rocm-smi invocation failed", exc_info=True)
        return {}
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        LOGGER.debug("Unable to parse rocm-smi JSON output")
        return {}

    results: Dict[str, Dict[str, Optional[int]]] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            if not isinstance(value, dict):
                continue
            total = _coerce_int(
                value.get("VRAM Total (MiB)")
                or value.get("vram_total")
                or value.get("total")
            )
            used = _coerce_int(
                value.get("VRAM Used (MiB)")
                or value.get("vram_used")
                or value.get("used")
            )
            free = _coerce_int(value.get("VRAM Free (MiB)") or value.get("vram_free") or value.get("free"))
            if total is not None and total < 8 * 1024**2:  # assume MiB
                total *= 1024 * 1024
            if used is not None and used < 8 * 1024**2:
                used *= 1024 * 1024
            if free is not None and free < 8 * 1024**2:
                free = max(0, free * 1024 * 1024)
            if free is None and total is not None and used is not None:
                free = max(total - used, 0)
            results[str(key)] = {"total": total, "free": free}
    return results


def _vendor_name(vendor_id: Optional[str]) -> str:
    if not vendor_id:
        return "Unknown"
    vendor_id = vendor_id.strip().lower()
    if vendor_id in {value.lower() for value in _AMD_VENDOR_IDS}:
        return "AMD"
    if vendor_id in {value.lower() for value in _NVIDIA_VENDOR_IDS}:
        return "NVIDIA"
    if vendor_id in {value.lower() for value in _INTEL_VENDOR_IDS}:
        return "Intel"
    return vendor_id


def _driver_name(device_dir: Path) -> str:
    driver_link = device_dir / "driver"
    if driver_link.exists():
        try:
            return driver_link.resolve().name
        except Exception:  # pragma: no cover - best effort
            return driver_link.name
    return "unknown"


def _parse_key_value(path: Path) -> Dict[str, str]:
    content = _read_text(path)
    if not content:
        return {}
    result: Dict[str, str] = {}
    for line in content.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except OSError:  # pragma: no cover - permission errors, etc.
        LOGGER.debug("Unable to read %s", path, exc_info=True)
        return None


def _read_int(path: Path) -> Optional[int]:
    text = _read_text(path)
    if text is None:
        return None
    return _coerce_int(text)


def _coerce_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        if isinstance(value, str):
            value = value.strip()
            if value.lower().startswith("0x"):
                return int(value, 16)
        return int(value)
    except (TypeError, ValueError):
        return None


def _format_name(name: Optional[str], vendor: str, bus_id: Optional[str], driver: str) -> str:
    base = name or vendor or driver or "GPU"
    if vendor and vendor not in base:
        base = f"{vendor} {base}".strip()
    if bus_id:
        return f"{base} ({bus_id})"
    return base


__all__ = [
    "AcceleratorInfo",
    "detect_accelerators",
    "total_vram_bytes",
    "recommend_models_for_vram",
]
