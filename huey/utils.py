# huey/utils.py

import logging
from .exceptions import InvalidInputError


def setup_logging(config):
    """Set up logging configuration based on the config dictionary."""
    level_name = config.get("logging", {}).get("level", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_file = config.get("logging", {}).get("file", "huey.log")

    logging.basicConfig(
        level=level,
        filename=log_file,
        filemode="a",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.info("Logging is set up.")


def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
    return a + b


def validate_input(value, expected_type):
    """Validate that the input is of the expected type."""
    if not isinstance(value, expected_type):
        raise InvalidInputError(f"Expected {expected_type}, got {type(value)} instead.")
    return True
