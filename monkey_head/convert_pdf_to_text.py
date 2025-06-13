# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
import os
from pypdf import PdfReader


def convert_pdf_to_text(pdf_file, output_file):
    """
    Converts a PDF file to a text file.

    Args:
        pdf_file (str): Path to the input PDF file.
        output_file (str): Path to the output text file.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        OSError: If there is an error reading the PDF file or writing the text file.
    """
    if not os.path.exists(pdf_file):
        raise FileNotFoundError(f"PDF file '{pdf_file}' not found.")

    try:
        with open(pdf_file, "rb") as file:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except OSError as e:
        raise OSError(f"Error reading PDF file '{pdf_file}': {e}")

    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(text)
    except OSError as e:
        raise OSError(f"Error writing text file '{output_file}': {e}")

    print(f"PDF converted to text and saved to '{output_file}'")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert a PDF file to a text file.")
    parser.add_argument("pdf_file", help="Path to the input PDF file.")
    parser.add_argument("output_file", help="Path to the output text file.")
    args = parser.parse_args()

    try:
        convert_pdf_to_text(args.pdf_file, args.output_file)
    except Exception as e:
        print(f"Error: {e}")
