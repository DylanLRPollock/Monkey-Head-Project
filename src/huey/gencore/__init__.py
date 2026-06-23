"""GenCore AI/OS kernel primitives for HueyOS."""

from __future__ import annotations

from .boot import BootSequence, BootStage
from .device_manager import DeviceManager, DeviceProfile
from .interrupts import Interrupt, InterruptController
from .kernel import GenCoreKernel
from .memory import MemoryManager, MemoryPage
from .modules import KernelModule, ModuleLoader
from .process import ProcessDescriptor, ProcessManager
from .scheduler import ScheduledTask, TaskScheduler
from .syscalls import SyscallRegistry

__all__ = [
    "BootSequence",
    "BootStage",
    "DeviceManager",
    "DeviceProfile",
    "GenCoreKernel",
    "Interrupt",
    "InterruptController",
    "KernelModule",
    "MemoryManager",
    "MemoryPage",
    "ModuleLoader",
    "ProcessDescriptor",
    "ProcessManager",
    "ScheduledTask",
    "SyscallRegistry",
    "TaskScheduler",
]
