# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Sync Pygpt Structure module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Synchronize pygpt-MHP submodule files with the local project.

The script copies files from ``repo/pygpt-MHP`` into the main repository so
modules can be imported directly from ``src``. Existing files will only be
overwritten if they contain a ``Placeholder for`` header. The ``--depth``
option controls how deep into the submodule the copy process recurses. By
default the entire tree is mirrored.
"""
import os
import shutil
import argparse


PYGPT_DIR = os.path.join("repo", "pygpt-MHP")
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def _should_copy_file(dst: str) -> bool:
    """Return True if ``dst`` does not exist or contains a placeholder header."""
    if not os.path.exists(dst):
        return True

    try:
        with open(dst, "r", errors="ignore") as f:
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                cleaned = line.lstrip("# ").strip()
                if cleaned.startswith("Placeholder for"):
                    return True
        return False
    except Exception:
        return False


def sync(src: str, dst: str, depth: int | None = None) -> None:
    """Copy file or directory from src to dst if missing or placeholder."""
    if os.path.isdir(src):
        os.makedirs(dst, exist_ok=True)
        if depth is None or depth > 0:
            for item in os.listdir(src):
                sync(
                    os.path.join(src, item),
                    os.path.join(dst, item),
                    None if depth is None else depth - 1,
                )
    else:
        if _should_copy_file(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


def mirror_tree(src_root: str, dst_root: str, depth: int | None = None) -> None:
    for item in os.listdir(src_root):
        src_path = os.path.join(src_root, item)
        dst_path = os.path.join(dst_root, item)
        sync(src_path, dst_path, None if depth is None else depth - 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Copy files from the pygpt-MHP submodule into the main project"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        help="Limit recursion depth when copying (default: unlimited)",
    )
    args = parser.parse_args()
    mirror_tree(PYGPT_DIR, ROOT_DIR, depth=args.depth)
