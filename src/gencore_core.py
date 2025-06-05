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
    except Exception as e:
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
        input_data = json.loads(args.input_data)
        core_data = process_core_data(input_data)
        print(json.dumps(core_data, indent=4))
    except Exception as e:
        print(f"Error: {e}")
