# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import logging


class ErrorHandler:
    def __init__(self, log_file="app.log"):
        logging.basicConfig(filename=log_file, level=logging.INFO)

    def log_error(self, error_message):
        logging.error(error_message)

    def log_info(self, info_message):
        logging.info(info_message)

    def handle_exception(self, exception):
        self.log_error(f"Exception occurred: {exception}")
        # Additional error handling logic
