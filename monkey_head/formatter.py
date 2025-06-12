# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
def format_text(text, line_length=80):
    """
    Formats a text string to a specified line length.

    Args:
        text (str): The text to format.
        line_length (int): The maximum length of each line. Default is 80.

    Returns:
        str: The formatted text.
    """
    words = text.split()
    formatted_text = ""
    line = ""

    for word in words:
        if len(line) + len(word) + 1 > line_length:
            formatted_text += line.strip() + "\n"
            line = ""
        line += word + " "

    formatted_text += line.strip()
    return formatted_text


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Format a text string to a specified line length."
    )
    parser.add_argument("text", help="The text to format.")
    parser.add_argument(
        "--line_length", type=int, default=80, help="The maximum length of each line."
    )
    args = parser.parse_args()

    try:
        formatted_text = format_text(args.text, args.line_length)
        print(formatted_text)
    except Exception as e:
        print(f"Error: {e}")
