# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Exceptions module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
# huey/exceptions.py


class HueyError(Exception):
    """Base exception class for Huey project."""

    pass


class DataNotFoundError(HueyError):
    """Exception raised when expected data is not found."""

    pass


class InvalidInputError(HueyError):
    """Exception raised for invalid input."""

    pass
