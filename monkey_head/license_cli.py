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


def show_license_cli(config_path: str | Path = "config/pygpt_net/config.json") -> None:
    """Display license text in the terminal and prompt for acceptance."""
    manager = ConfigManager(str(config_path))
    if manager.get_setting("license.accepted"):
        return

    try:
        license_text = Path("docs/LICENSE").read_text(encoding="utf-8")
    except Exception:
        license_text = "License file not found."

    print(license_text)
    response = input("Do you accept the license terms? [y/N]: ").strip().lower()
    if response in {"y", "yes"}:
        accept_license(config_path)
    else:
        raise RuntimeError("License not accepted")


if __name__ == "__main__":
    show_license_cli()
