# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
"""Utility for splitting a text file into individual chapter files."""
import os


def split_chapters(input_file, output_dir):
    """
    Splits a text file into chapters based on a delimiter and saves each chapter as a separate file.

    Args:
        input_file (str): Path to the input text file.
        output_dir (str): Directory to save the chapter files.

    Raises:
        FileNotFoundError: If the input file does not exist.
        OSError: If there is an error creating the output directory or writing files.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found.")

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except OSError as e:
            raise OSError(f"Error creating output directory '{output_dir}': {e}")

    try:
        with open(input_file, "r", encoding="utf-8") as file:
            content = file.read()
    except OSError as e:
        raise OSError(f"Error reading input file '{input_file}': {e}")

    chapters = content.split("CHAPTER")
    for i, chapter in enumerate(chapters):
        chapter_file = os.path.join(output_dir, f"chapter_{i + 1}.txt")
        try:
            with open(chapter_file, "w", encoding="utf-8") as file:
                file.write(chapter.strip())
        except OSError as e:
            raise OSError(f"Error writing chapter file '{chapter_file}': {e}")

    print(f"Chapters split and saved to '{output_dir}'")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Split a text file into chapters.")
    parser.add_argument("input_file", help="Path to the input text file.")
    parser.add_argument("output_dir", help="Directory to save the chapter files.")
    args = parser.parse_args()

    try:
        split_chapters(args.input_file, args.output_dir)
    except Exception as e:
        print(f"Error: {e}")
