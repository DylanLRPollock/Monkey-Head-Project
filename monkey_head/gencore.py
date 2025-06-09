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
def generate_core_data(input_data):
    """
    Generates core data based on the input data.

    Args:
        input_data (dict): The input data.

    Returns:
        dict: The generated core data.
    """
    core_data = {}
    try:
        # Example logic for generating core data
        core_data["processed"] = True
        core_data["input_length"] = len(input_data)
        core_data["details"] = input_data
        logger.debug("Core data generated successfully")
    except Exception as e:
        logger.exception("Error generating core data")
        raise ValueError(f"Error generating core data: {e}")

    return core_data


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Generate core data based on the input data."
    )
    parser.add_argument("input_data", help="The input data in JSON format.")
    args = parser.parse_args()

    try:
        input_data = json.loads(args.input_data)
        core_data = generate_core_data(input_data)
        output = json.dumps(core_data, indent=4)
        print(output)
        logger.info(output)
    except Exception as e:
        logger.exception("Error generating core data from CLI")
        print(f"Error: {e}")
