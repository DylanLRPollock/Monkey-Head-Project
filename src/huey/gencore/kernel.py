"""Top-level GenCore kernel that wires the speculative subsystem tree."""

from __future__ import annotations

from typing import Any

from huey.settings import RuntimeSettings

from .boot import BootSequence
from .device_manager import DeviceManager
from .interrupts import Interrupt, InterruptController
from .memory import MemoryManager
from .modules import KernelModule, ModuleLoader
from .process import ProcessManager
from .scheduler import TaskScheduler
from .syscalls import SyscallRegistry


class GenCoreKernel:
    """Coordinate bootstrapping, syscalls, memory, and logical devices."""

    def __init__(self, settings: RuntimeSettings | None = None) -> None:
        self.settings = settings or RuntimeSettings.from_env()
        self.scheduler = TaskScheduler()
        self.memory = MemoryManager()
        self.processes = ProcessManager()
        self.interrupts = InterruptController()
        self.syscalls = SyscallRegistry()
        self.boot = BootSequence()
        self.modules = ModuleLoader()
        self.devices = DeviceManager()
        self.boot_log: list[dict[str, object]] = []
        self.booted = False
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.boot.add_stage(
            "load-settings",
            "Load environment and runtime settings.",
            lambda: bool(self.settings.environment),
        )
        self.boot.add_stage(
            "register-syscalls",
            "Expose internal kernel services via syscalls.",
            lambda: self._register_syscalls(),
        )
        self.boot.add_stage(
            "register-modules",
            "Activate the baseline GenCore modules.",
            lambda: self._register_modules(),
        )
        self.boot.add_stage(
            "discover-devices",
            "Create logical device records for kernel-visible peripherals.",
            lambda: self._register_devices(),
        )
        self.interrupts.register_handler(
            "memory.flush",
            lambda interrupt: self.memory.release(
                str(interrupt.payload["key"]),
                namespace=str(interrupt.payload.get("namespace", "global")),
            ),
        )

    def _register_syscalls(self) -> bool:
        self.syscalls.register("memory.put", self.memory.allocate)
        self.syscalls.register("memory.get", self.memory.lookup)
        self.syscalls.register("process.spawn", self.processes.spawn)
        self.syscalls.register("scheduler.schedule", self.scheduler.schedule)
        self.syscalls.register("kernel.snapshot", self.snapshot)
        self.syscalls.register("devices.inventory", self.devices.inventory)
        return True

    def _register_modules(self) -> bool:
        if self.modules.inventory():
            return True
        self.modules.register(
            KernelModule("scheduler", provides=("task-queue", "priorities"))
        )
        self.modules.register(KernelModule("memory", provides=("allocation", "cache")))
        self.modules.register(
            KernelModule("governance", provides=("policies", "audit-routing"))
        )
        self.modules.register(KernelModule("network", provides=("api", "messaging")))
        return True

    def _register_devices(self) -> bool:
        if self.devices.inventory():
            return True
        self.devices.register_device(
            "cortex-bus",
            "virtual-backplane",
            metadata={"profile": self.settings.boot_profile},
        )
        self.devices.register_device(
            "sensor-grid",
            "telemetry-array",
            metadata={"enabled": self.settings.hardware_enabled},
        )
        for device in ("cortex-bus", "sensor-grid"):
            self.devices.set_status(device, "online")
        return True

    def bootstrap(self) -> list[dict[str, object]]:
        self.boot_log = self.boot.run()
        self.booted = True
        return list(self.boot_log)

    def create_process(
        self, name: str, *, metadata: dict[str, object] | None = None
    ) -> dict[str, object]:
        return self.processes.spawn(name, metadata=metadata).as_dict()

    def schedule_task(
        self,
        name: str,
        *,
        priority: int = 100,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return self.scheduler.schedule(name, priority=priority, payload=payload).as_dict()

    def emit_interrupt(
        self, code: str, source: str, payload: dict[str, object] | None = None
    ) -> object | None:
        return self.interrupts.dispatch(
            Interrupt(code=code, source=source, payload=dict(payload or {}))
        )

    def run_cycle(self) -> dict[str, object]:
        completed = [task.as_dict() for task in self.scheduler.run_all(limit=10)]
        return {
            "booted": self.booted,
            "completed_tasks": completed,
            "processes": self.processes.list_processes(),
            "memory_used": self.memory.used_capacity,
        }

    def health_report(self) -> dict[str, object]:
        return {
            "status": "ok" if self.booted else "boot-pending",
            "booted": self.booted,
            "devices_online": len(self.devices.online_devices()),
            "modules_active": len(self.modules.active_modules()),
            "syscalls": self.syscalls.list_syscalls(),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "settings": self.settings.to_dict(),
            "booted": self.booted,
            "boot_log": list(self.boot_log),
            "memory": self.memory.snapshot(),
            "processes": self.processes.list_processes(),
            "devices": self.devices.inventory(),
            "modules": self.modules.inventory(),
            "syscalls": self.syscalls.list_syscalls(),
            "interrupts": self.interrupts.history(),
            "pending_tasks": [task.as_dict() for task in self.scheduler.pending()],
        }


__all__ = ["GenCoreKernel"]
