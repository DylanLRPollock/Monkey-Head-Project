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
    except Exception as e:
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
        print(json.dumps(core_data, indent=4))
    except Exception as e:
        print(f"Error: {e}")
