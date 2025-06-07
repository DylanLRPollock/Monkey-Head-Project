# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import os
import shutil

PYGPT_DIR = os.path.join('repo', 'pygpt-MHP')
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def _should_copy_file(dst: str) -> bool:
    """Return True if file should be copied from the source."""
    if not os.path.exists(dst):
        return True
    try:
        with open(dst, "r", errors="ignore") as f:
            first = f.readline().strip()
        return first.startswith("Placeholder for")
    except Exception:
        return False


def sync(src: str, dst: str, depth: int = 0) -> None:
    """Copy file or directory from src to dst if missing or placeholder."""
    if os.path.isdir(src):
        os.makedirs(dst, exist_ok=True)
        if depth > 0:
            for item in os.listdir(src):
                sync(
                    os.path.join(src, item),
                    os.path.join(dst, item),
                    depth=depth - 1,
                )
    else:
        if _should_copy_file(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


def mirror_tree(src_root: str, dst_root: str, depth: int = 1) -> None:
    for item in os.listdir(src_root):
        src_path = os.path.join(src_root, item)
        dst_path = os.path.join(dst_root, item)
        sync(src_path, dst_path, depth=depth - 1)

if __name__ == "__main__":
    mirror_tree(PYGPT_DIR, ROOT_DIR, depth=2)

