# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Huey Remover module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
import os


def remove_files(directory, extension, *, dry_run=False):
    """
    Removes files with a specific extension from a directory.

    Args:
        directory (str): The directory to remove files from.
        extension (str): The file extension to remove.
        dry_run (bool): When True, only report which files would be removed.

    Raises:
        FileNotFoundError: If the directory does not exist.
        OSError: If there is an error removing the files.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory '{directory}' not found.")

    removed = []
    try:
        for filename in os.listdir(directory):
            if filename.endswith(extension):
                file_path = os.path.join(directory, filename)
                removed.append(file_path)
                if dry_run:
                    print(f"[dry-run] Would remove file: {file_path}")
                    continue
                os.remove(file_path)
                print(f"Removed file: {file_path}")
    except OSError as e:
        raise OSError(f"Error removing files in '{directory}': {e}") from e
    return removed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Remove files with a specific extension from a directory."
    )
    parser.add_argument("directory", help="The directory to remove files from.")
    parser.add_argument("extension", help="The file extension to remove.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would be removed without deleting them.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive confirmation prompt.",
    )
    args = parser.parse_args()

    try:
        if not args.dry_run and not args.yes:
            confirmation = input(
                f"Remove '*{args.extension}' files from '{args.directory}'? [y/N]: "
            ).strip().lower()
            if confirmation not in {"y", "yes"}:
                print("Cancelled.")
                raise SystemExit(1)
        remove_files(args.directory, args.extension, dry_run=args.dry_run)
    except Exception as e:
        print(f"Error: {e}")
