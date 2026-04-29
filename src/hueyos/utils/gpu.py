"""GPU and accelerator discovery helpers used by tests and API summaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class AcceleratorInfo:
    name: str
    vendor: str
    driver: str = "unknown"
    backend: str = "unknown"
    vram_total: int | None = None
    vram_free: int | None = None
    bus_id: str | None = None
    node: str | None = None

    def to_dict(self) -> dict[str, object]:
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


_VENDORS = {
    "0x1002": ("AMD", "rocm"),
    "0x10de": ("NVIDIA", "cuda"),
    "0x8086": ("Intel", "openvino"),
}


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _read_int(path: Path) -> int | None:
    value = _read_text(path)
    if value is None:
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def _read_uevent_value(path: Path, key: str) -> str | None:
    content = _read_text(path)
    if not content:
        return None
    prefix = f"{key}="
    for line in content.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip() or None
    return None


def detect_accelerators(
    sys_root: str | Path = "/sys/class/drm",
) -> list[AcceleratorInfo]:
    """Detect DRM accelerator devices from a sysfs-style tree."""

    root = Path(sys_root)
    if not root.is_dir():
        return []

    accelerators: list[AcceleratorInfo] = []
    for device_dir in sorted(root.glob("card*/device")):
        vendor_id = (_read_text(device_dir / "vendor") or "").lower()
        vendor, backend = _VENDORS.get(vendor_id, ("Unknown", "unknown"))
        total = _read_int(device_dir / "mem_info_vram_total")
        used = _read_int(device_dir / "mem_info_vram_used") or 0
        free = max(total - used, 0) if total is not None else None
        node = device_dir.parent.name
        bus_id = _read_uevent_value(device_dir / "uevent", "PCI_SLOT_NAME")

        accelerators.append(
            AcceleratorInfo(
                name=f"{vendor} accelerator" if vendor != "Unknown" else node,
                vendor=vendor,
                backend=backend,
                vram_total=total,
                vram_free=free,
                bus_id=bus_id,
                node=node,
            )
        )
    return accelerators


def total_vram_bytes(accelerators: Iterable[AcceleratorInfo]) -> int:
    return sum(info.vram_total or 0 for info in accelerators)


def recommend_models_for_vram(vram_bytes: int | None) -> list[str]:
    """Return conservative local model recommendations for available VRAM."""

    gib = (vram_bytes or 0) / 1024**3
    if gib >= 40:
        return ["llama3.1:70b", "mixtral:8x22b", "qwen2.5:32b"]
    if gib >= 16:
        return ["llama3.1:8b", "mistral-nemo:12b", "qwen2.5:14b"]
    if gib >= 8:
        return ["llama3.2:3b", "mistral:7b", "phi3:mini"]
    return ["tinyllama:1.1b", "phi3:mini", "gemma2:2b"]


__all__ = [
    "AcceleratorInfo",
    "detect_accelerators",
    "recommend_models_for_vram",
    "total_vram_bytes",
]
