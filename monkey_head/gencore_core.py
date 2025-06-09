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
def process_core_data(input_data):
    """
    Processes the input data to generate core data.

    Args:
        input_data (dict): The input data.

    Returns:
        dict: The processed core data.
    """
    core_data = {}
    try:
        # Example logic for processing core data
        core_data["processed"] = True
        core_data["input_length"] = len(input_data)
        core_data["details"] = {k: v for k, v in input_data.items() if v is not None}
        logger.debug("Core data processed successfully")
    except Exception as e:
        logger.exception("Error processing core data")
        raise ValueError(f"Error processing core data: {e}")

    return core_data


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Process the input data to generate core data."
    )
    parser.add_argument("input_data", help="The input data in JSON format.")
    args = parser.parse_args()

    try:
        input_json = json.loads(args.input_data)
        core_data = process_core_data(input_json)
        output = json.dumps(core_data, indent=4)
        print(output)
        logger.info(output)
    except Exception as e:
        logger.exception("Error processing core data from CLI")
        print(f"Error: {e}")
