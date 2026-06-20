"""Dependency tracking for runtime startup and health ordering."""

from __future__ import annotations


class DependencyGraph:
    """Track service dependencies and compute safe startup order."""

    def __init__(self) -> None:
        self._dependencies: dict[str, set[str]] = {}

    def register(
        self, service: str, depends_on: list[str] | tuple[str, ...] = ()
    ) -> None:
        self._dependencies.setdefault(service, set()).update(depends_on)
        for dependency in depends_on:
            self._dependencies.setdefault(dependency, set())

    def add_dependency(self, service: str, dependency: str) -> None:
        self.register(service, (dependency,))

    def dependencies_for(self, service: str) -> list[str]:
        return sorted(self._dependencies.get(service, set()))

    def dependents_for(self, service: str) -> list[str]:
        return sorted(
            name
            for name, dependencies in self._dependencies.items()
            if service in dependencies
        )

    def startup_order(self) -> list[str]:
        dependencies = {
            name: set(values) for name, values in self._dependencies.items()
        }
        order: list[str] = []
        ready = sorted(name for name, values in dependencies.items() if not values)
        while ready:
            current = ready.pop(0)
            order.append(current)
            for dependent in self.dependents_for(current):
                remaining = dependencies[dependent]
                remaining.discard(current)
                if not remaining and dependent not in order and dependent not in ready:
                    ready.append(dependent)
                    ready.sort()
        unresolved = {name: values for name, values in dependencies.items() if values}
        if unresolved:
            raise ValueError(f"Dependency cycle detected: {unresolved}")
        return order

    def as_dict(self) -> dict[str, list[str]]:
        return {
            name: sorted(values) for name, values in sorted(self._dependencies.items())
        }


__all__ = ["DependencyGraph"]
