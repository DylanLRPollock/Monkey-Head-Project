"""Logical device inventory for HueyOS hardware attachments."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DeviceProfile:
    name: str
    kind: str
    status: str = "offline"
    metadata: dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "status": self.status,
            "metadata": dict(self.metadata),
        }


class DeviceManager:
    """Track logical devices participating in the runtime."""

    def __init__(self) -> None:
        self._devices: dict[str, DeviceProfile] = {}

    def register_device(
        self, name: str, kind: str, *, metadata: dict[str, object] | None = None
    ) -> DeviceProfile:
        profile = DeviceProfile(name=name, kind=kind, metadata=dict(metadata or {}))
        self._devices[name] = profile
        return profile

    def set_status(self, name: str, status: str) -> DeviceProfile:
        profile = self._devices[name]
        profile.status = status
        return profile

    def online_devices(self) -> list[dict[str, object]]:
        return [
            profile.as_dict()
            for profile in sorted(self._devices.values(), key=lambda item: item.name)
            if profile.status == "online"
        ]

    def inventory(self) -> list[dict[str, object]]:
        return [
            profile.as_dict()
            for profile in sorted(self._devices.values(), key=lambda item: item.name)
        ]


__all__ = ["DeviceManager", "DeviceProfile"]
