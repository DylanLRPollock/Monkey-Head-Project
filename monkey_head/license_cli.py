# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Command-line license acceptance helper."""
from pathlib import Path

from .license_gui import accept_license
from .config_manager import ConfigManager
from .error_handler import ErrorHandler


def load_license_text(license_path: str | Path = "docs/LICENSE") -> str:
    """Return the license text or a fallback message."""
    try:
        return Path(license_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return "License file not found."
    except Exception as exc:  # pragma: no cover - unexpected errors
        ErrorHandler().handle_exception(exc)
        return "License file not available." 


def prompt_response() -> bool:
    """Prompt user for license acceptance and validate the response."""
    for _ in range(3):
        response = input("Do you accept the license terms? [y/N]: ").strip().lower()
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no", ""}:
            return False
        print("Please respond with 'y' or 'n'.")
    return False


def show_license_cli(
    config_path: str | Path = "config/pygpt_net/config.json",
    license_path: str | Path = "docs/LICENSE",
) -> None:
    """Display license text in the terminal and prompt for acceptance."""
    try:
        manager = ConfigManager(str(config_path))
    except Exception as exc:
        raise RuntimeError(f"Failed to load config: {exc}") from exc

    if manager.get_setting("license.accepted"):
        return

    print(load_license_text(license_path))
    if prompt_response():
        accept_license(config_path)
    else:
        raise RuntimeError("License not accepted")


if __name__ == "__main__":
    show_license_cli()
