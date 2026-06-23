"""Simplified storage manager used for tests."""

from __future__ import annotations

import shutil
import time
from pathlib import Path


class StorageManager:
    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _ensure_dir(self, name: str) -> Path:
        target = self.base_path / name
        target.mkdir(parents=True, exist_ok=True)
        return target

    def sort_root_files(self) -> None:
        for item in self.base_path.iterdir():
            if item.is_file():
                suffix = item.suffix.lstrip(".").upper() or "MISC"
                dest_dir = self._ensure_dir(suffix)
                shutil.move(str(item), dest_dir / item.name)

    def list_files(self, folder: str) -> list[str]:
        path = self.base_path / folder
        if not path.exists():
            return []
        return [str(p) for p in path.iterdir() if p.is_file()]

    def cleanup_empty_dirs(self) -> None:
        for path, dirnames, filenames in self.base_path.walk(top_down=False):
            if not dirnames and not filenames:
                path.rmdir()

    def get_total_size(self) -> int:
        total = 0
        for path, _dirnames, filenames in self.base_path.walk():
            for filename in filenames:
                fp = path / filename
                total += fp.stat().st_size
        return total

    def remove_older_than(self, days: int) -> int:
        threshold = time.time() - days * 86400
        removed = 0
        for path, _dirnames, filenames in self.base_path.walk():
            for filename in filenames:
                fp = path / filename
                if fp.stat().st_mtime < threshold:
                    fp.unlink()
                    removed += 1
        self.cleanup_empty_dirs()
        return removed


__all__ = ["StorageManager"]
