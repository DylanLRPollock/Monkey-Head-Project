"""Kernel module registration and lifecycle helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from huey.exceptions import KernelModuleError


@dataclass(slots=True)
class KernelModule:
    name: str
    version: str = "0.1.0"
    provides: tuple[str, ...] = field(default_factory=tuple)
    enabled: bool = True
    metadata: dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "provides": list(self.provides),
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }


class ModuleLoader:
    """Manage kernel module metadata."""

    def __init__(self) -> None:
        self._modules: dict[str, KernelModule] = {}

    def register(self, module: KernelModule) -> KernelModule:
        if module.name in self._modules:
            raise KernelModuleError(f"Module already registered: {module.name}")
        self._modules[module.name] = module
        return module

    def enable(self, name: str) -> KernelModule:
        module = self._modules[name]
        module.enabled = True
        return module

    def disable(self, name: str) -> KernelModule:
        module = self._modules[name]
        module.enabled = False
        return module

    def active_modules(self) -> list[dict[str, object]]:
        return [
            module.as_dict()
            for module in sorted(self._modules.values(), key=lambda item: item.name)
            if module.enabled
        ]

    def inventory(self) -> list[dict[str, object]]:
        return [
            module.as_dict()
            for module in sorted(self._modules.values(), key=lambda item: item.name)
        ]


__all__ = ["KernelModule", "ModuleLoader"]
