"""Fault-tolerance helpers for replicated storage plans."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ReplicationPolicy:
    replicas: int = 3
    quorum: int = 2

    def plan(self, cluster: str) -> dict[str, object]:
        nodes = [f"{cluster}-node-{index}" for index in range(1, self.replicas + 1)]
        return {"cluster": cluster, "replicas": nodes, "quorum": self.quorum}


__all__ = ["ReplicationPolicy"]
