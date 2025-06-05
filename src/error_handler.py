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
