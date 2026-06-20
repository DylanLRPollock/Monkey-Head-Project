"""Registry of runtime services, dependencies, and health metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

ServiceHealthcheck = Callable[[], dict[str, object] | bool | str | None]


@dataclass
class ServiceRecord:
    name: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    status: str = "unknown"
    kind: str = "service"
    metadata: dict[str, object] = field(default_factory=dict)
    healthcheck: ServiceHealthcheck | None = field(
        default=None, repr=False, compare=False
    )

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "dependencies": list(self.dependencies),
            "status": self.status,
            "kind": self.kind,
            "metadata": dict(self.metadata),
        }


class ServiceRegistry:
    """Track runtime services and expose serializable summaries."""

    def __init__(self) -> None:
        self._services: dict[str, ServiceRecord] = {}

    def register(self, record: ServiceRecord) -> ServiceRecord:
        self._services[record.name] = record
        return record

    def register_service(
        self,
        name: str,
        description: str,
        *,
        dependencies: list[str] | tuple[str, ...] = (),
        status: str = "unknown",
        kind: str = "service",
        metadata: dict[str, object] | None = None,
        healthcheck: ServiceHealthcheck | None = None,
    ) -> ServiceRecord:
        return self.register(
            ServiceRecord(
                name=name,
                description=description,
                dependencies=list(dependencies),
                status=status,
                kind=kind,
                metadata=dict(metadata or {}),
                healthcheck=healthcheck,
            )
        )

    def get(self, name: str) -> ServiceRecord:
        return self._services[name]

    def update_status(
        self,
        name: str,
        status: str,
        *,
        metadata: dict[str, object] | None = None,
    ) -> ServiceRecord:
        record = self.get(name)
        record.status = status
        if metadata:
            record.metadata.update(metadata)
        return record

    def all(self) -> list[ServiceRecord]:
        return [self._services[name] for name in sorted(self._services)]

    def ready_services(self) -> list[ServiceRecord]:
        return [record for record in self.all() if record.status == "ready"]

    def as_dict(self) -> dict[str, dict[str, object]]:
        return {record.name: record.as_dict() for record in self.all()}


__all__ = ["ServiceRecord", "ServiceRegistry"]
