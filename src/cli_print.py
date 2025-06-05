def print_message(message, message_type="info"):
    """
    Prints a message to the console with a specific format based on the message type.

    Args:
        message (str): The message to print.
        message_type (str): The type of message ('info', 'warning', 'error'). Default is 'info'.

    Raises:
        ValueError: If the message_type is not one of 'info', 'warning', or 'error'.
    """
    if message_type == "info":
        print(f"[INFO] {message}")
    elif message_type == "warning":
        print(f"[WARNING] {message}")
    elif message_type == "error":
        print(f"[ERROR] {message}")
    else:
        raise ValueError(
            f"Invalid message_type '{message_type}'. Expected 'info', 'warning', or 'error'."
        )


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
