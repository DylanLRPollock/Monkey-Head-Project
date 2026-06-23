"""Bridge logical kernel devices to hardware hubs."""

from __future__ import annotations

from huey.gencore.kernel import GenCoreKernel
from huey.hardware.actuators import ActuatorHub
from huey.hardware.sensors import SensorHub


class HardwareBridge:
    """Publish hardware inventory into the kernel snapshot."""

    def __init__(
        self,
        kernel: GenCoreKernel,
        *,
        sensors: SensorHub | None = None,
        actuators: ActuatorHub | None = None,
    ) -> None:
        self.kernel = kernel
        self.sensors = sensors or SensorHub()
        self.actuators = actuators or ActuatorHub()

    def snapshot(self) -> dict[str, object]:
        return {
            "devices": self.kernel.devices.inventory(),
            "sensors": self.sensors.inventory(),
            "actuators": self.actuators.inventory(),
        }


__all__ = ["HardwareBridge"]
