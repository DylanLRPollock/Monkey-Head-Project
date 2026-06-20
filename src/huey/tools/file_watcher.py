"""Filesystem monitoring helpers based on snapshot diffs."""

from __future__ import annotations

from pathlib import Path


class FileWatcher:
    """Snapshot a directory tree and report changed files."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._snapshot: dict[str, float] = {}

    def snapshot(self) -> dict[str, float]:
        self._snapshot = {
            str(path.relative_to(self.root)): path.stat().st_mtime
            for path in self.root.rglob("*")
            if path.is_file()
        }
        return dict(self._snapshot)

    def changes(self) -> dict[str, list[str]]:
        current = {
            str(path.relative_to(self.root)): path.stat().st_mtime
            for path in self.root.rglob("*")
            if path.is_file()
        }
        added = [path for path in current if path not in self._snapshot]
        removed = [path for path in self._snapshot if path not in current]
        modified = [
            path
            for path, timestamp in current.items()
            if path in self._snapshot and self._snapshot[path] != timestamp
        ]
        self._snapshot = current
        return {
            "added": sorted(added),
            "removed": sorted(removed),
            "modified": sorted(modified),
        }


__all__ = ["FileWatcher"]
