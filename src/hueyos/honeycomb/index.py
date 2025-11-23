# www.dlrp.ca
# HueyOS: Honeycomb Index module (hueyos)

"""Content aware indexing helpers for :class:`HoneycombStorage`."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Optional, Sequence

from hueyos.honeycomb.storage import HoneycombRecord, HoneycombStorage
from hueyos.utils.auto_sort import get_extension_map


@dataclass(frozen=True)
class HoneycombContentMapping:
    """Describe how a high level content type maps onto the honeycomb."""

    comb: str
    cell_prefix: str
    categories: Sequence[str]
    description: str = ""
    retention: Optional[str] = None

    def prefixes(self) -> List[str]:
        """Return full key prefixes managed by this mapping."""

        base = f"{self.comb}/{self.cell_prefix}"
        return [f"{base}/"]


_DEFAULT_MAPPINGS: Dict[str, HoneycombContentMapping] = {
    "images": HoneycombContentMapping(
        comb="media",
        cell_prefix="images",
        categories=("JPEG", "PNG"),
        description="Raster and photographic imagery including JPEG and PNG payloads.",
    ),
    "documents": HoneycombContentMapping(
        comb="knowledge",
        cell_prefix="documents",
        categories=("PDF", "MD", "TXT", "DOC", "PPT", "XLS"),
        description="Research notes, PDFs, spreadsheets and other knowledge artefacts.",
    ),
    "logs": HoneycombContentMapping(
        comb="telemetry",
        cell_prefix="logs",
        categories=("LOG", "JSON"),
        description="Structured and unstructured log output captured from systems.",
    ),
    "sensor": HoneycombContentMapping(
        comb="telemetry",
        cell_prefix="sensor",
        categories=("CSV", "JSON"),
        description="Sensor derived timeseries and JSON snapshots from the field.",
    ),
    "archives": HoneycombContentMapping(
        comb="packages",
        cell_prefix="archives",
        categories=("ZIP", "GZ"),
        description="Compressed backups and data bundles stored for posterity.",
    ),
    "code": HoneycombContentMapping(
        comb="knowledge",
        cell_prefix="code",
        categories=("PY", "SH"),
        description="Executable snippets and scripts relevant to Honeycomb operations.",
    ),
}


class HoneycombIndex:
    """Resolve content types into deterministic honeycomb storage locations."""

    def __init__(
        self,
        storage: HoneycombStorage,
        *,
        mappings: Optional[Mapping[str, HoneycombContentMapping]] = None,
        extension_map: Optional[Mapping[str, str]] = None,
    ) -> None:
        self._storage = storage
        self._mappings: Dict[str, HoneycombContentMapping] = dict(
            mappings or _DEFAULT_MAPPINGS
        )
        self._extension_map: Mapping[str, str] = extension_map or get_extension_map()
        self._category_index: MutableMapping[str, str] = {}
        self._rebuild_category_index()

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------
    def _rebuild_category_index(self) -> None:
        self._category_index.clear()
        for content_type, mapping in self._mappings.items():
            for category in mapping.categories:
                self._category_index.setdefault(category.upper(), content_type)

    def register_content_type(
        self, name: str, mapping: HoneycombContentMapping
    ) -> None:
        """Register or replace a mapping for ``name``."""

        self._mappings[name] = mapping
        self._rebuild_category_index()

    def list_content_types(self) -> List[str]:
        """Return the known content type identifiers."""

        return sorted(self._mappings.keys())

    def get_mapping(self, content_type: str) -> HoneycombContentMapping:
        """Return the mapping for ``content_type`` raising ``KeyError`` when unknown."""

        return self._mappings[content_type]

    def prefixes_for_content_type(self, content_type: str) -> List[str]:
        """Return the honeycomb prefixes associated with ``content_type``."""

        mapping = self._mappings[content_type]
        return mapping.prefixes()

    # ------------------------------------------------------------------
    # Classification helpers
    # ------------------------------------------------------------------
    def infer_category(self, path: Path) -> Optional[str]:
        """Return the auto-sort category for ``path`` when possible."""

        if path.suffix:
            extension = path.suffix.lower().lstrip(".")
        else:
            extension = ""
        category = self._extension_map.get(extension)
        if category:
            return category.upper()
        if extension:
            return extension.upper()
        return None

    def infer_content_type(self, path: Path) -> Optional[str]:
        """Return the logical content type for ``path`` if it is known."""

        category = self.infer_category(path)
        if category is None:
            return None
        return self._category_index.get(category)

    # ------------------------------------------------------------------
    # Storage integration
    # ------------------------------------------------------------------
    def _build_key(
        self, mapping: HoneycombContentMapping, *, cell_id: Optional[str] = None
    ) -> str:
        cell = cell_id or uuid.uuid4().hex
        return f"{mapping.comb}/{mapping.cell_prefix}/{cell}"

    def store_payload(
        self,
        content_type: str,
        payload: Dict[str, object],
        *,
        cell_id: Optional[str] = None,
        retention: Optional[str] = None,
    ) -> HoneycombRecord:
        """Store a payload under a generated honeycomb key."""

        mapping = self._mappings[content_type]
        if retention is None:
            retention = mapping.retention
        payload = {
            "content_type": content_type,
            "payload": payload,
            "retention": retention,
            "created_at": time.time(),
        }
        key = self._build_key(mapping, cell_id=cell_id)
        return self._storage.store(key, payload)

    def ingest_file(
        self, path: Path, *, retention: Optional[str] = None
    ) -> HoneycombRecord:
        """Store a file under a generated honeycomb key."""

        content_type = self.infer_content_type(path)
        if content_type is None:
            raise ValueError("Unknown content type for path")
        payload = {
            "filename": path.name,
            "path": str(path),
            "ingested_at": time.time(),
        }
        return self.store_payload(content_type, payload, retention=retention)

    def list_content(self, content_type: str) -> List[HoneycombRecord]:
        """Return records stored under ``content_type``."""

        mapping = self._mappings[content_type]
        prefix = f"{mapping.comb}/{mapping.cell_prefix}"
        return list(self._storage.iter_records(prefix=prefix))


__all__ = ["HoneycombContentMapping", "HoneycombIndex"]
