"""Memory allocation helpers for the lightweight GenCore kernel."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from huey.constants import DEFAULT_MEMORY_CAPACITY


def _estimate_size(value: object) -> int:
    try:
        payload = json.dumps(value, sort_keys=True, default=str)
    except TypeError:
        payload = repr(value)
    return max(1, len(payload))


@dataclass(slots=True)
class MemoryPage:
    key: str
    value: Any
    namespace: str = "global"
    size: int = 1

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "namespace": self.namespace,
            "size": self.size,
            "value": self.value,
        }


class MemoryManager:
    """Track small in-memory allocations for kernel services."""

    def __init__(self, *, capacity: int = DEFAULT_MEMORY_CAPACITY) -> None:
        self.capacity = capacity
        self._pages: dict[tuple[str, str], MemoryPage] = {}

    @property
    def used_capacity(self) -> int:
        return sum(page.size for page in self._pages.values())

    def allocate(
        self, key: str, value: Any, *, namespace: str = "global"
    ) -> MemoryPage:
        page = MemoryPage(
            key=key,
            value=value,
            namespace=namespace,
            size=_estimate_size(value),
        )
        self._pages[(namespace, key)] = page
        return page

    def lookup(self, key: str, *, namespace: str = "global") -> Any | None:
        page = self._pages.get((namespace, key))
        return None if page is None else page.value

    def release(self, key: str, *, namespace: str = "global") -> MemoryPage | None:
        return self._pages.pop((namespace, key), None)

    def namespaces(self) -> list[str]:
        return sorted({namespace for namespace, _ in self._pages})

    def snapshot(self) -> dict[str, object]:
        return {
            "capacity": self.capacity,
            "used_capacity": self.used_capacity,
            "pages": [page.as_dict() for page in self._pages.values()],
        }


__all__ = ["MemoryManager", "MemoryPage"]
