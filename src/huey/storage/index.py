"""Secondary indexing helpers for honeycomb storage."""

from __future__ import annotations


class StorageIndex:
    """Track key membership by label and cluster."""

    def __init__(self) -> None:
        self._labels: dict[str, set[str]] = {}
        self._clusters: dict[str, set[str]] = {}

    def add(self, key: str, *, labels: list[str] | None = None, cluster: str = "") -> None:
        for label in labels or []:
            self._labels.setdefault(label, set()).add(key)
        if cluster:
            self._clusters.setdefault(cluster, set()).add(key)

    def remove(self, key: str) -> None:
        for bucket in self._labels.values():
            bucket.discard(key)
        for bucket in self._clusters.values():
            bucket.discard(key)

    def by_label(self, label: str) -> list[str]:
        return sorted(self._labels.get(label, set()))

    def by_cluster(self, cluster: str) -> list[str]:
        return sorted(self._clusters.get(cluster, set()))

    def snapshot(self) -> dict[str, object]:
        return {
            "labels": {label: sorted(values) for label, values in self._labels.items()},
            "clusters": {
                cluster: sorted(values) for cluster, values in self._clusters.items()
            },
        }


__all__ = ["StorageIndex"]
