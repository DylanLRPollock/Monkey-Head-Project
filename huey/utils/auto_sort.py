# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Auto Sort module (huey/utils)

"""Utilities for organising files stored in the shared memory directory."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Mapping

from ..function_registry import register_function
from .paths import get_memory_path

_EXTENSION_MAP: Dict[str, str] = {
    "bat": "BAT",
    "csv": "CSV",
    "doc": "DOC",
    "docx": "DOC",
    "gz": "GZ",
    "jpeg": "JPEG",
    "jpg": "JPEG",
    "json": "JSON",
    "log": "LOG",
    "md": "MD",
    "mp4": "MP4",
    "pdf": "PDF",
    "png": "PNG",
    "ppt": "PPT",
    "pptx": "PPT",
    "py": "PY",
    "sh": "SH",
    "txt": "TXT",
    "xls": "XLS",
    "xlsx": "XLS",
    "yaml": "YAML",
    "yml": "YAML",
    "zip": "ZIP",
}


def get_extension_map() -> Mapping[str, str]:
    """Return a read-only view of the extension to category mapping."""

    return _EXTENSION_MAP.copy()


def _normalise_destination_root(destination: str | Path | None) -> Path:
    base = get_memory_path(create=True)
    if destination is None:
        return base
    destination_path = Path(destination)
    if not destination_path.is_absolute():
        destination_path = base / destination_path
    destination_path.mkdir(parents=True, exist_ok=True)
    return destination_path


def _normalise_source(source: str | Path | None) -> Path:
    base = get_memory_path(create=True)
    if source is None:
        source_path = base / "RAW"
    else:
        source_path = Path(source)
        if not source_path.is_absolute():
            source_path = base / source_path
    return source_path.resolve()


def _determine_target_dir(path: Path) -> str:
    if path.suffix:
        ext = path.suffix.lower().lstrip(".")
    else:
        ext = ""
    return _EXTENSION_MAP.get(ext, ext.upper() if ext else "MISC")


@register_function
def auto_sort_memory(
    source_dir: str | Path | None = None,
    destination_root: str | Path | None = None,
    dry_run: bool = False,
) -> Dict[str, Iterable[str]]:
    """Organise files from ``source_dir`` into typed folders under ``destination_root``.

    Parameters
    ----------
    source_dir:
        Directory containing unsorted files. Defaults to ``memory/RAW`` relative to
        the resolved memory directory.
    destination_root:
        Destination directory that will receive the typed subdirectories. Defaults
        to the resolved memory directory.
    dry_run:
        When ``True`` the function only reports the planned moves without
        modifying the filesystem.

    Returns
    -------
    dict
        A summary containing the moved and skipped files.
    """

    source_path = _normalise_source(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_path}")

    destination_path = _normalise_destination_root(destination_root)

    moved: List[str] = []
    skipped: List[str] = []

    for item in sorted(source_path.iterdir()):
        if not item.is_file():
            continue
        target_dir_name = _determine_target_dir(item)
        target_dir = destination_path / target_dir_name
        target_dir.mkdir(parents=True, exist_ok=True)
        destination_file = target_dir / item.name
        if destination_file.exists():
            skipped.append(item.name)
            continue
        if dry_run:
            moved.append(f"{item.name} -> {target_dir_name}/{item.name}")
            continue
        item.replace(destination_file)
        moved.append(str(destination_file.relative_to(destination_path)))

    return {
        "source": str(source_path),
        "destination": str(destination_path),
        "moved": moved,
        "skipped": skipped,
    }
