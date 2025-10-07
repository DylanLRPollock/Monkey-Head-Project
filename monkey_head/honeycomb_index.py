"""Content aware indexing helpers for :class:`HoneycombStorage`."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from monkey_head.honeycomb_storage import HoneycombRecord, HoneycombStorage
from monkey_head.utils.auto_sort import get_extension_map


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

    def register_content_type(self, name: str, mapping: HoneycombContentMapping) -> None:
        """Register or replace a mapping for ``name``."""

        self._mappings[name] = mapping
        self._rebuild_category_index()

    def list_content_types(self) -> List[str]:
        """Return the known content type identifiers."""

        return sorted(self._mappings.keys())

    def get_mapping(self, content_type: str) -> HoneycombContentMapping:
        """Return the mapping for ``content_type`` raising ``KeyError`` when unknown."""

        return self._mappings[content_type]

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
    def _build_key(self, mapping: HoneycombContentMapping, *, cell_id: Optional[str] = None) -> str:
        cell = cell_id or uuid.uuid4().hex
        return f"{mapping.comb}/{mapping.cell_prefix}/{cell}"

    def store_payload(
        self,
        content_type: str,
        payload: Dict[str, object],
        *,
        metadata: Optional[Dict[str, object]] = None,
        cell_id: Optional[str] = None,
    ) -> HoneycombRecord:
        """Persist ``payload`` under the path defined for ``content_type``."""

        mapping = self.get_mapping(content_type)
        record_payload = {
            "content_type": content_type,
            "payload": payload,
            "metadata": metadata or {},
            "indexed_at": time.time(),
        }
        key = self._build_key(mapping, cell_id=cell_id)
        return self._storage.store(key, record_payload)

    def index_file(
        self,
        path: Path,
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> HoneycombRecord:
        """Record metadata about ``path`` into the honeycomb."""

        resolved = Path(path).resolve()
        inferred = content_type or self.infer_content_type(resolved)
        mapping_type = inferred or "misc"
        mapping = self._mappings.get(mapping_type)
        if mapping is None:
            mapping = HoneycombContentMapping(
                comb="misc",
                cell_prefix="general",
                categories=(),
                description="Fallback bucket for unclassified artefacts.",
            )
            self._mappings[mapping_type] = mapping
            self._rebuild_category_index()
        payload = {
            "path": str(resolved),
            "name": resolved.name,
            "suffix": resolved.suffix,
            "category": self.infer_category(resolved),
            "content_type": mapping_type,
        }
        payload.update(metadata or {})
        return self.store_payload(mapping_type, payload)

    def prefixes_for_content_type(self, content_type: str) -> Iterable[str]:
        """Return storage prefixes used by ``content_type``."""

        mapping = self.get_mapping(content_type)
        return mapping.prefixes()

    def describe(self) -> Dict[str, Dict[str, object]]:
        """Return a serialisable description of the registered mappings."""

        description: Dict[str, Dict[str, object]] = {}
        for name, mapping in self._mappings.items():
            description[name] = {
                "comb": mapping.comb,
                "cell_prefix": mapping.cell_prefix,
                "categories": list(mapping.categories),
                "description": mapping.description,
                "retention": mapping.retention,
            }
        return description


__all__ = [
    "HoneycombContentMapping",
    "HoneycombIndex",
]
