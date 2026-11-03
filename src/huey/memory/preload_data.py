"""Preload configured memory data and curated prompt assets, never scripts."""

from __future__ import annotations

import csv
from pathlib import Path

from huey.utils.paths import get_memory_path

_HUEY_DIR = Path(__file__).resolve().parents[1]
_PROMPT_CANDIDATES = (
    _HUEY_DIR / "memory" / "CSV" / "pygpt_prompts.csv",
    _HUEY_DIR / "connectors" / "pyhuey" / "data" / "prompts.csv",
)
_NON_DATA_DIRS = {"PY", "__pycache__", ".git", ".venv", "INDEX"}


def load_prompts() -> list[dict[str, str]]:
    """Load first available prompt CSV, handling comment-only header lines."""

    prompts_file = next((p for p in _PROMPT_CANDIDATES if p.is_file()), None)
    if prompts_file is None:
        return []
    with prompts_file.open(encoding="utf-8-sig", newline="") as handle:
        line = next(handle, "")
        while line.startswith("#") or not line.strip():
            line = next(handle, "")
            if not line:
                return []
        return list(csv.DictReader([line, *handle]))


def load_memory() -> dict[str, list[str]]:
    """List top-level data files; never return the legacy Python source tree."""

    root = get_memory_path(create=False)
    if not root.is_dir():
        return {}
    result: dict[str, list[str]] = {}
    for directory in sorted(root.iterdir()):
        if not directory.is_dir() or directory.is_symlink():
            continue
        if directory.name.startswith(".") or directory.name in _NON_DATA_DIRS:
            continue
        paths = sorted(
            str(path.resolve())
            for path in directory.iterdir()
            if path.is_file()
            and not path.is_symlink()
            and not path.name.startswith(".")
            and path.suffix.lower() != ".py"
        )
        if paths:
            result[directory.name] = paths
    return result


def preload_all() -> dict[str, object]:
    return {"prompts": load_prompts(), "memory": load_memory()}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Preload memory and prompts")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    data = preload_all()
    if args.summary:
        print(f"Prompts loaded: {len(data['prompts'])}")
        for category, files in data["memory"].items():
            print(f"{category}: {len(files)} files")
    else:
        print(data)


if __name__ == "__main__":
    main()
