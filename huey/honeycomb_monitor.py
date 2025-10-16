# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Honeycomb Monitor module (huey)

"""Monitoring helpers for analysing honeycomb memory utilisation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from monkey_head.honeycomb_index import HoneycombIndex
from monkey_head.honeycomb_storage import HoneycombStorage


@dataclass(frozen=True)
class HoneycombUsageTotals:
    """Aggregate totals derived from the honeycomb usage metrics."""

    cells: int
    payload_bytes: int
    combs: int
    last_update: Optional[float]


class HoneycombMonitor:
    """Compute summary metrics describing how the honeycomb is being used."""

    def __init__(
        self,
        storage: HoneycombStorage,
        *,
        index: Optional[HoneycombIndex] = None,
    ) -> None:
        self._storage = storage
        self._index = index

    def _content_type_summary(self) -> List[Dict[str, object]]:
        if self._index is None:
            return []
        summary: List[Dict[str, object]] = []
        for content_type in self._index.list_content_types():
            aggregates = {
                "content_type": content_type,
                "cells": 0,
                "payload_bytes": 0,
                "oldest": None,
                "newest": None,
            }
            for prefix in self._index.prefixes_for_content_type(content_type):
                metrics = self._storage.prefix_metrics(prefix)
                aggregates["cells"] += metrics["cells"]
                aggregates["payload_bytes"] += metrics["payload_bytes"]
                oldest = aggregates["oldest"]
                newest = aggregates["newest"]
                metrics_oldest = metrics.get("oldest")
                metrics_newest = metrics.get("newest")
                if metrics_oldest is not None and (
                    oldest is None or metrics_oldest < oldest
                ):
                    aggregates["oldest"] = metrics_oldest
                if metrics_newest is not None and (
                    newest is None or metrics_newest > newest
                ):
                    aggregates["newest"] = metrics_newest
            summary.append(aggregates)
        return summary

    def usage_totals(self, comb_usage: Iterable[Dict[str, object]]) -> HoneycombUsageTotals:
        cells = 0
        payload_bytes = 0
        combs = 0
        last_update: Optional[float] = None
        for comb in comb_usage:
            cells += int(comb.get("cells", 0))
            payload_bytes += int(comb.get("payload_bytes", 0))
            combs += 1
            newest = comb.get("newest")
            if newest is not None and (last_update is None or newest > last_update):
                last_update = float(newest)
        return HoneycombUsageTotals(
            cells=cells,
            payload_bytes=payload_bytes,
            combs=combs,
            last_update=last_update,
        )

    def build_usage_report(self, *, window_days: int = 30) -> Dict[str, object]:
        """Return a structured overview of honeycomb usage suitable for dashboards."""

        comb_usage = self._storage.comb_usage()
        totals = self.usage_totals(comb_usage)
        content_types = self._content_type_summary()
        growth = self._storage.growth_samples(window_days)
        return {
            "summary": comb_usage,
            "totals": {
                "cells": totals.cells,
                "payload_bytes": totals.payload_bytes,
                "combs": totals.combs,
                "last_update": totals.last_update,
            },
            "content_types": content_types,
            "growth": growth,
        }

    def dashboard_payload(self, *, window_days: int = 30) -> Dict[str, object]:
        """Alias for :meth:`build_usage_report` for readability."""

        return self.build_usage_report(window_days=window_days)


__all__ = ["HoneycombMonitor", "HoneycombUsageTotals"]
