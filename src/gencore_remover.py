# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import os


def remove_files(directory, extension):
    """
    Removes files with a specific extension from a directory.

    Args:
        directory (str): The directory to remove files from.
        extension (str): The file extension to remove.

    Raises:
        FileNotFoundError: If the directory does not exist.
        OSError: If there is an error removing the files.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory '{directory}' not found.")

    try:
        for filename in os.listdir(directory):
            if filename.endswith(extension):
                file_path = os.path.join(directory, filename)
                os.remove(file_path)
                print(f"Removed file: {file_path}")
    except OSError as e:
        raise OSError(f"Error removing files in '{directory}': {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Remove files with a specific extension from a directory."
    )
    parser.add_argument("directory", help="The directory to remove files from.")
    parser.add_argument("extension", help="The file extension to remove.")
    args = parser.parse_args()

    try:
        remove_files(args.directory, args.extension)
    except Exception as e:
        print(f"Error: {e}")
