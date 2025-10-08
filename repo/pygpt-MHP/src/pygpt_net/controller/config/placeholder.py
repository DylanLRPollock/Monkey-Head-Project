"""Placeholder utilities mirrored from the PyGPT configuration tree."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


class Placeholder:
    """Provide minimal preset discovery compatible with PyGPT widgets."""

    def __init__(self, window: Any) -> None:
        self.window = window

    def _iter_presets(self) -> Iterable[tuple[str, Any]]:
        core = getattr(self.window, "core", None)
        presets = getattr(core, "presets", None)
        if presets is None:
            return []
        try:
            items = presets.get_all()
        except Exception:  # pragma: no cover - defensive fallback
            return []
        if isinstance(items, dict):
            return items.items()
        return []

    def get_presets(self) -> List[Dict[str, str]]:
        """Return presets formatted for selector widgets."""

        results: List[Dict[str, str]] = [{"_": "---"}]
        for filename, preset in self._iter_presets():
            name = getattr(preset, "name", str(filename))
            results.append({str(filename): str(name)})
        return results


__all__ = ["Placeholder"]
