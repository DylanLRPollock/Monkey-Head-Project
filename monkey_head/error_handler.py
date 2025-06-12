# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.09.2025
# ==================================================
import logging
from .logging_setup import configure_logging


class ErrorHandler:
    def __init__(self, log_file="app.log"):
        # Initialize logging if not already configured
        logger = configure_logging()
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            logger.addHandler(file_handler)

    def log_error(self, error_message):
        logging.error(error_message)

    def log_info(self, info_message):
        logging.info(info_message)

    def handle_exception(self, exception):
        self.log_error(f"Exception occurred: {exception}")
        # Additional error handling logic
