#!/usr/bin/env python3
"""Generate a Markdown repository map for the current checkout."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _should_skip(path: Path) -> bool:
    return path.name.startswith(".") or path.name == "__pycache__"


def _tree_lines(root: Path, *, max_depth: int, depth: int = 0) -> list[str]:
    if depth > max_depth:
        return []
    indent = "  " * depth
    lines = [f"{indent}- {root.name}/" if root.is_dir() else f"{indent}- {root.name}"]
    if root.is_file() or depth == max_depth:
        return lines
    children = [child for child in sorted(root.iterdir()) if not _should_skip(child)]
    for child in children:
        lines.extend(_tree_lines(child, max_depth=max_depth, depth=depth + 1))
    return lines


def build_repository_map(root: Path, *, max_depth: int = 3) -> str:
    """Return a Markdown repository map."""

    sections = []
    for name in ("src", "tests", "scripts", "docs", "integrations"):
        target = root / name
        if target.exists():
            sections.append(
                f"## {name}\n\n" + "\n".join(_tree_lines(target, max_depth=max_depth))
            )
    header = "# Repository Map\n\nGenerated from the current checkout.\n"
    return header + "\n\n".join(sections) + "\n"


def write_repository_map(path: Path, *, root: Path, max_depth: int = 3) -> Path:
    """Write the repository map to disk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_repository_map(root, max_depth=max_depth), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate docs/repository-map.md")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="docs/repository-map.md")
    parser.add_argument("--max-depth", type=int, default=3)
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    write_repository_map(output, root=root, max_depth=args.max_depth)
    print(f"Wrote repository map to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
