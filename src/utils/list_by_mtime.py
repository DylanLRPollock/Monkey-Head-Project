import os
from typing import List


def list_files_by_mtime(directory: str) -> List[str]:
    """Return file paths sorted by modification time (oldest first)."""
    entries = [os.path.join(directory, f) for f in os.listdir(directory)]
    entries = [e for e in entries if os.path.isfile(e)]
    entries.sort(key=lambda p: os.path.getmtime(p))
    return entries


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="List files in a directory from oldest to newest"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan",
    )
    args = parser.parse_args()

    for file_path in list_files_by_mtime(args.directory):
        print(file_path)
