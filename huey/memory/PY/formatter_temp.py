# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Formatter Temp module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.09.2025
# ==================================================
import os
import sys
import glob
import atexit
import logging
from ..logging_setup import configure_logging
import json
from concurrent.futures import ThreadPoolExecutor
from nltk.tokenize import sent_tokenize


# Define Formatter class
class Formatter:
    def __init__(self, encoding="utf-8", config_file="formatter_config.json"):
        self.encoding = encoding
        self.load_config(config_file)
        self.setup_logging()
        self.initial_message()
        self.initial_variable()
        self.folder_checks()
        atexit.register(self.graceful_exit)

    # Load configuration from file
    def load_config(self, config_file):
        try:
            with open(config_file, "r") as file:
                config = json.load(file)
                self.books_folder = config.get("books_folder", "BOOKS")
                self.memory_folder = config.get("memory_folder", "MEMORY")
                self.splitter_folder = config.get("splitter_folder", "SPLITTER")
        except FileNotFoundError:
            self.books_folder = "BOOKS"
            self.memory_folder = "MEMORY"
            self.splitter_folder = "SPLITTER"

    # Setup logging configuration
    def setup_logging(self):
        """Configure logging for the formatter utility."""
        logger = configure_logging()
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.baseFilename = "formatter.log"

    # Initialize important variables
    def initial_variable(self):
        self.program_name = os.path.abspath(__file__)
        self.current_folder = os.path.dirname(os.path.abspath(__file__))
        self.parent_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.books_folder = os.path.join(self.parent_folder, self.books_folder)
        self.memory_folder = os.path.join(self.parent_folder, self.memory_folder)
        self.splitter_folder = os.path.join(self.parent_folder, self.splitter_folder)

    # Handles resource cleanup and program exit
    def graceful_exit(self):
        self.print_message("Cleaning up resources...", "status")
        self.print_message("Exiting the program.", "status")
        sys.exit()

    # Check and create required folders
    def folder_checks(self):
        self.print_message("Scanning 'BOOKS' folder for new files...", "status")
        self.ensure_folder_exists(self.books_folder)
        self.print_message("Scanning 'MEMORY' folder...", "status")
        self.ensure_folder_exists(self.memory_folder)
        self.print_message("Scanning 'SPLITTER' folder...", "status")
        self.ensure_folder_exists(self.splitter_folder)

    # Display initial messages
    def initial_message(self):
        program_name = os.path.basename(__file__).replace(".py", "")
        formatted_program_name = " ".join(
            word.capitalize() for word in program_name.split("_")
        )
        title_message = f"[Initialization] Monkey Head Project: {formatted_program_name} Initialized"
        init_message = (f"Starting '{formatted_program_name}.py'...", "initialization")
        print(f"Monkey Head Project: Huey / BananaBrain - {formatted_program_name}")
        self.print_message(title_message, "initialization")
        self.print_message(init_message[0], init_message[1])

    # General-purpose message printing function
    def print_message(self, output_message, message_type):
        # Validation and Error Handling extracted to a separate function
        self.validate_print_message_input(output_message, message_type)
        # Actual message printing
        if message_type.lower() == "alert":
            output_message = (
                f"Alert has been triggered & program may fail!' {output_message}'"
            )
        if message_type.lower() == "user_input":
            return input(f"> {message_type.capitalize()}: {output_message}")
        else:
            print(f"> {message_type.capitalize()}: {output_message}")
            logging.info(f"{message_type.capitalize()}: {output_message}")

    # Validate the inputs to print_message function
    def validate_print_message_input(self, output_message, message_type):
        try:
            if not (isinstance(output_message, str) and isinstance(message_type, str)):
                raise TypeError("Invalid input types for print_message function.")
            elif not output_message.strip() or not message_type.strip():
                raise ValueError("Empty strings are not allowed.")
            valid_message_types = [
                "initialization",
                "status",
                "info",
                "error",
                "debug",
                "alert",
                "user_input",
                "query",
                "summary",
                "warning",
                "fatal_error",
                "shutdown",
            ]
            if message_type.lower() not in valid_message_types:
                raise ValueError("Invalid message_type provided.")
        except (TypeError, ValueError) as e:
            self.print_message(str(e), "error")
            self.graceful_exit()

    # Check if a folder exists, and create it if it doesn't
    def ensure_folder_exists(self, folder_name):
        folder_path = os.path.join(self.parent_folder, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    # Main function that orchestrates the text file processing
    def main(self):
        print("end")


# Create instance and run the main loop
if __name__ == "__main__":
    formatter = Formatter()
    formatter.main()
