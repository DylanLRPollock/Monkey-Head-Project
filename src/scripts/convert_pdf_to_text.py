# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import os
import PyPDF2
import logging
from concurrent.futures import ThreadPoolExecutor

# Setup logging configuration
logging.basicConfig(
    filename="convert_pdf_to_text.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Convert PDF to text
def convert_pdf_to_text(path):
    try:
        with open(path, "rb") as file:
            reader = PyPDF2.PdfFileReader(file)
            text = ""
            for page_num in range(reader.numPages):
                text += reader.getPage(page_num).extractText()
            logging.info(f"Successfully converted {path} to text.")
            return text
    except Exception as e:
        logging.error(f"Error converting {path} to text: {str(e)}")
        return str(e)


# Save text to file
def save_text_to_file(text, file_path):
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(text)
            logging.info(f"Successfully saved text to {file_path}.")
            return "OK"
    except Exception as e:
        logging.error(f"Error saving text to {file_path}: {str(e)}")
        return str(e)


# Process a single PDF file
def process_pdf(pdf_path, output_dir):
    text = convert_pdf_to_text(pdf_path)
    output_path = os.path.join(
        output_dir, os.path.basename(pdf_path).replace(".pdf", ".txt")
    )
    result = save_text_to_file(text, output_path)
    print(result)


# Process multiple PDF files in a directory
def process_pdfs_in_directory(input_dir, output_dir):
    pdf_files = [
        os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith(".pdf")
    ]
    with ThreadPoolExecutor() as executor:
        for pdf_file in pdf_files:
            executor.submit(process_pdf, pdf_file, output_dir)


if __name__ == "__main__":
    # Configuration
    input_dir = "pdf-input"
    output_dir = "pdf-output"

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Process PDFs
    process_pdfs_in_directory(input_dir, output_dir)
