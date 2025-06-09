# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
from .logger import get_logger

logger = get_logger(__name__)
def check_core_data(core_data):
    """
    Checks the validity of core data.

    Args:
        core_data (dict): The core data to check.

    Returns:
        bool: True if the core data is valid, False otherwise.
    """
    try:
        if not isinstance(core_data, dict):
            raise ValueError("Core data must be a dictionary.")
        if "processed" not in core_data or not core_data["processed"]:
            raise ValueError("Core data is not processed.")
        if "input_length" not in core_data or not isinstance(
            core_data["input_length"], int
        ):
            raise ValueError("Invalid input length in core data.")
        logger.debug("Core data validated successfully")
        return True
    except Exception as e:
        logger.exception("Error checking core data")
        print(f"Error checking core data: {e}")
        return False


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Check the validity of core data.")
    parser.add_argument("core_data", help="The core data in JSON format.")
    args = parser.parse_args()

    try:
        core_data = json.loads(args.core_data)
        is_valid = check_core_data(core_data)
        message = f"Core data is valid: {is_valid}"
        print(message)
        logger.info(message)
    except Exception as e:
        logger.exception("Error validating core data from CLI")
        print(f"Error: {e}")
