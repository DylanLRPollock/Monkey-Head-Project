"""Deterministic branch coverage for GenCore kernel primitives and wiring."""

from __future__ import annotations

import pytest

from huey.exceptions import KernelBootError, KernelModuleError
from huey.gencore.boot import BootSequence
from huey.gencore.device_manager import DeviceManager
from huey.gencore.interrupts import Interrupt, InterruptController
from huey.gencore.kernel import GenCoreKernel
from huey.gencore.memory import MemoryManager, _estimate_size
from huey.gencore.modules import KernelModule, ModuleLoader
from huey.gencore.process import ProcessManager
from huey.gencore.syscalls import SyscallRegistry
from huey.settings import RuntimeSettings


def test_boot_sequence_describe_optional_and_required_failure() -> None:
    sequence = BootSequence()
    sequence.add_stage("optional", "optional stage", lambda: False, required=False)
    sequence.add_stage("required", "required stage", lambda: True)
    assert sequence.describe() == [
        {"name": "optional", "description": "optional stage", "required": False},
        {"name": "required", "description": "required stage", "required": True},
    ]
    assert sequence.run() == [
        {
            "name": "optional",
            "description": "optional stage",
            "required": False,
            "ready": False,
        },
        {
            "name": "required",
            "description": "required stage",
            "required": True,
            "ready": True,
        },
    ]

    failing = BootSequence()
    failing.add_stage("required", "must pass", lambda: False)
    with pytest.raises(KernelBootError, match="Boot stage failed: required"):
        failing.run()


def test_memory_manager_estimate_capacity_and_release() -> None:
    manager = MemoryManager(capacity=64)
    manager.allocate("json", {"name": "Huey"})
    manager.allocate("fallback", {1: "one", "a": "two"}, namespace="custom")
    assert _estimate_size({1: "one", "a": "two"}) >= 1
    assert manager.lookup("json") == {"name": "Huey"}
    assert manager.lookup("missing") is None
    assert manager.namespaces() == ["custom", "global"]
    removed = manager.release("fallback", namespace="custom")
    assert removed is not None and removed.key == "fallback"
    assert manager.release("missing", namespace="custom") is None
    snapshot = manager.snapshot()
    assert snapshot["capacity"] == 64
    assert snapshot["used_capacity"] == manager.used_capacity
    assert snapshot["pages"][0]["key"] == "json"


def test_module_loader_rejects_duplicates_and_filters_active_modules() -> None:
    loader = ModuleLoader()
    loader.register(KernelModule("alpha", provides=("queue",)))
    with pytest.raises(KernelModuleError, match="Module already registered: alpha"):
        loader.register(KernelModule("alpha"))
    loader.register(KernelModule("beta"))
    loader.disable("beta")
    assert [module["name"] for module in loader.active_modules()] == ["alpha"]
    assert [module["name"] for module in loader.inventory()] == ["alpha", "beta"]
    assert loader.enable("beta").enabled is True


def test_process_interrupt_device_and_syscall_helpers() -> None:
    processes = ProcessManager()
    descriptor = processes.spawn("worker", metadata={"role": "batch"})
    assert descriptor.state == "running"
    assert processes.mark_waiting(descriptor.pid).state == "waiting"
    assert processes.terminate(descriptor.pid).state == "stopped"
    assert processes.list_processes()[0]["metadata"] == {"role": "batch"}

    devices = DeviceManager()
    devices.register_device("zeta", "virtual")
    devices.register_device("alpha", "sensor")
    devices.set_status("alpha", "online")
    assert [device["name"] for device in devices.inventory()] == ["alpha", "zeta"]
    assert [device["name"] for device in devices.online_devices()] == ["alpha"]

    interrupts = InterruptController()
    interrupts.register_handler("power.low", lambda interrupt: interrupt.payload["percent"])
    assert interrupts.dispatch(Interrupt("unknown", "tests")) is None
    assert (
        interrupts.dispatch(
            Interrupt("power.low", "tests", payload={"percent": 11})
        )
        == 11
    )
    assert [item["code"] for item in interrupts.history()] == ["unknown", "power.low"]

    syscalls = SyscallRegistry()
    syscalls.register("sum", lambda a, b=0: a + b)
    syscalls.register("noop", lambda: None)
    assert syscalls.invoke("sum", 2, b=5) == 7
    assert syscalls.list_syscalls() == ["noop", "sum"]


def test_gencore_kernel_bootstrap_cycle_interrupts_and_snapshot() -> None:
    settings = RuntimeSettings(
        environment="test",
        boot_profile="minimal",
        hardware_enabled=True,
    )
    kernel = GenCoreKernel(settings=settings)
    assert kernel.health_report()["status"] == "boot-pending"

    boot_log = kernel.bootstrap()
    assert kernel.booted is True
    assert [entry["name"] for entry in boot_log] == [
        "load-settings",
        "register-syscalls",
        "register-modules",
        "discover-devices",
    ]
    assert all(entry["ready"] is True for entry in boot_log)

    health = kernel.health_report()
    assert health["status"] == "ok"
    assert health["devices_online"] == 2
    assert health["modules_active"] == 4
    assert "memory.put" in health["syscalls"]

    first_pid = kernel.create_process("dispatcher", metadata={"source": "tests"})["pid"]
    second_pid = kernel.create_process("worker")["pid"]
    assert second_pid == first_pid + 1

    scheduled = kernel.syscalls.invoke(
        "scheduler.schedule",
        "priority-work",
        priority=1,
        payload={"value": 9},
        handler=lambda payload: payload["value"] * 2,
    )
    assert scheduled.name == "priority-work"

    kernel.schedule_task("normal-work", priority=10, payload={"value": 1})
    cycle = kernel.run_cycle()
    assert cycle["booted"] is True
    assert [task["name"] for task in cycle["completed_tasks"]] == [
        "priority-work",
        "normal-work",
    ]
    assert cycle["completed_tasks"][0]["result"] == 18
    assert cycle["memory_used"] == kernel.memory.used_capacity
    assert len(cycle["processes"]) == 2

    kernel.memory.allocate("cache", {"ok": True}, namespace="flush")
    released = kernel.emit_interrupt(
        "memory.flush", "tests", {"key": "cache", "namespace": "flush"}
    )
    assert released is not None and released.key == "cache"
    assert kernel.emit_interrupt("unknown.interrupt", "tests", {"x": 1}) is None

    kernel._register_modules()
    kernel._register_devices()
    snapshot = kernel.snapshot()
    assert snapshot["settings"]["environment"] == "test"
    assert snapshot["booted"] is True
    assert snapshot["pending_tasks"] == []
    assert any(item["code"] == "unknown.interrupt" for item in snapshot["interrupts"])
