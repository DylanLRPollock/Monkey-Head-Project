# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: License Cli module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
from pathlib import Path

from .config_manager import ConfigManager
from .error_handler import ErrorHandler

DEFAULT_CONFIG = "config/pygpt_net/config.json"
LICENSE_PATH = "docs/LICENSE"


def load_license_text(path: str | Path = LICENSE_PATH) -> str:
    """Load license text from file, logging errors if not found."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:  # pragma: no cover - log and fallback
        ErrorHandler().handle_exception(e)
        return "License file not found."


def prompt_response(prompt: str) -> str:
    """Prompt the user repeatedly until 'yes' or 'no' is entered."""
    while True:  # pragma: no cover - loops until valid input
        try:
            answer = input(prompt).strip().lower()
        except Exception as e:  # pragma: no cover - log and retry
            ErrorHandler().handle_exception(e)
            print("Error reading input. Please try again.")
            continue
        if answer in {"y", "yes"}:
            return "yes"
        if answer in {"n", "no"}:
            return "no"
        print("Please respond with 'yes' or 'no'.")


def show_license_cli(config_path: str | Path = DEFAULT_CONFIG) -> None:
    """Display license text and prompt for acceptance on the command line."""
    manager = ConfigManager(str(config_path))
    if manager.get_setting("license.accepted"):
        return

    print(load_license_text())
    response = prompt_response("Do you accept the license terms? [y/n]: ")
    if response == "yes":
        manager.set_setting("license.accepted", True)
        print("WARNING: This is experimental software. Proceed with caution.")
    else:
        raise RuntimeError("License declined")


if __name__ == "__main__":  # pragma: no cover - manual execution
    show_license_cli()
