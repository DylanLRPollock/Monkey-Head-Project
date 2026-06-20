"""Motherboard inventory and diagnostics helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class MotherboardProfile:
    vendor: str = "Supermicro"
    model: str = "GenCore-X"
    firmware_version: str = "0.1.0"
    slots: dict[str, str] = field(
        default_factory=lambda: {
            "pcie_1": "available",
            "pcie_2": "available",
            "m2_1": "optane-ready",
        }
    )

    def diagnostics(self) -> dict[str, object]:
        return {
            "vendor": self.vendor,
            "model": self.model,
            "firmware_version": self.firmware_version,
            "slots": dict(self.slots),
        }


__all__ = ["MotherboardProfile"]
