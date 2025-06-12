#!/usr/bin/env python3
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
import json
import logging
from ..logging_setup import configure_logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


def valid_types():
    return ["status", "alert", "error", "debug", "user_input", "info", "warning"]


class CLI:
    valid_message_types = valid_types()

    def __init__(self, config_file="cli_config.json"):
        self.load_config(config_file)
        self.setup_logging()

    def load_config(self, config_file):
        try:
            with open(config_file, "r") as file:
                config = json.load(file)
                self.log_file = config.get("log_file", "CLI_LOG.json")
                self.valid_message_types = config.get(
                    "valid_message_types", valid_types()
                )
        except FileNotFoundError:
            self.log_file = "CLI_LOG.json"
            self.valid_message_types = valid_types()

    def setup_logging(self):
        """Configure logging for CLI output."""
        logger = configure_logging()
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.baseFilename = self.log_file

    def log_message(self, message, message_type):
        logging.log(
            level=getattr(logging, message_type.upper(), logging.INFO), msg=message
        )

    def print_message(self, output_message, message_type):
        self.validate_print_message_input(output_message, message_type)

        prefixes = {
            "alert": "Alert has been triggered & program may fail!",
            "user_input": "> {}",
            "default": "> {}",
        }

        prefix = prefixes.get(message_type.lower(), prefixes["default"])

        formatted_message = prefix.format(
            f"{message_type.capitalize()}: {output_message}"
        )

        self.log_message(formatted_message, message_type)

        if message_type.lower() == "user_input":
            return input(formatted_message)
        else:
            print(formatted_message)
            return None

    def handle_exception(self, error_type, function_name):
        self.print_message(
            f"Function '{function_name}' encountered a {error_type.__name__}.", "debug"
        )
        self.print_message("Manual oversight required!", "alert")
        self.graceful_exit()

    def graceful_exit(self):
        self.print_message("Cleaning up resources...", "status")
        self.print_message("Exiting the program.", "status")
        sys.exit()

    def validate_print_message_input(self, output_message, message_type):
        try:
            if not isinstance(output_message, str):
                raise TypeError("output_message must be a string.")
            if not output_message.strip():
                raise ValueError("output_message cannot be an empty string.")
            if not isinstance(message_type, str):
                raise TypeError("message_type must be a string.")
            if not message_type.strip():
                raise ValueError("message_type cannot be an empty string.")
            if message_type.lower() not in self.valid_message_types:
                raise ValueError(
                    f"Invalid message_type provided. Valid types are {', '.join(self.valid_message_types)}"
                )
        except (TypeError, ValueError) as e:
            self.print_message(str(e), "error")
            self.graceful_exit()

    def process_messages(self, messages):
        with ThreadPoolExecutor() as executor:
            for message, message_type in messages:
                executor.submit(self.print_message, message, message_type)


if __name__ == "__main__":
    cli = CLI()
    cli.print_message(
        f"DO NOT RUN THIS APPLICATION ON ITS OWN! ('{sys.argv[0]}')", "alert"
    )
