# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
import logging
from .utils.logger import get_logger


logger = get_logger(__name__)


def print_message(message, message_type="info"):
    """Print ``message`` to stdout and log it.

    Parameters
    ----------
    message:
        Text to display.
    message_type:
        One of ``"info"``, ``"warning"``, or ``"error"``. Defaults to ``"info"``.

    Raises
    ------
    ValueError
        If ``message_type`` is not recognised.
    """

    level_map = {
        "info": "INFO",
        "warning": "WARNING",
        "error": "ERROR",
    }
    level_name = level_map.get(message_type)
    if level_name is None:
        raise ValueError(
            f"Invalid message_type '{message_type}'. Expected 'info', 'warning', or 'error'."
        )
    logger.log(getattr(logging, level_name), message)
    print(f"[{level_name}] {message}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Print a message to the console.")
    parser.add_argument("message", help="The message to print.")
    parser.add_argument(
        "--type",
        choices=["info", "warning", "error"],
        default="info",
        help="The type of message.",
    )
    args = parser.parse_args()

    try:
        print_message(args.message, args.type)
    except Exception as e:
        print(f"Error: {e}")
