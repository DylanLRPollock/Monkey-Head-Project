# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Huey Disk Manager Temp module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
import os
import shutil


def manage_temp_files(temp_dir, action):
    """
    Manages temporary files in a specified directory.

    Args:
        temp_dir (str): The directory containing temporary files.
        action (str): The action to perform ('delete' or 'archive').

    Raises:
        ValueError: If the action is not 'delete' or 'archive'.
        OSError: If there is an error performing the action.
    """
    if not os.path.exists(temp_dir):
        raise FileNotFoundError(f"Temporary directory '{temp_dir}' not found.")

    if action not in ["delete", "archive"]:
        raise ValueError("Action must be 'delete' or 'archive'.")

    try:
        if action == "delete":
            shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            print(f"Temporary files in '{temp_dir}' deleted.")
        elif action == "archive":
            archive_dir = temp_dir + "_archive"
            shutil.move(temp_dir, archive_dir)
            os.makedirs(temp_dir)
            print(f"Temporary files in '{temp_dir}' archived to '{archive_dir}'.")
    except OSError as e:
        raise OSError(f"Error managing temporary files in '{temp_dir}': {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage temporary files in a specified directory."
    )
    parser.add_argument("temp_dir", help="The directory containing temporary files.")
    parser.add_argument(
        "action",
        choices=["delete", "archive"],
        help="The action to perform ('delete' or 'archive').",
    )
    args = parser.parse_args()

    try:
        manage_temp_files(args.temp_dir, args.action)
    except Exception as e:
        print(f"Error: {e}")
