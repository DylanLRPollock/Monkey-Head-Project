# huey/main.py

import logging
from .utils import setup_logging, calculate_sum, validate_input
from .config import load_config
from .exceptions import InvalidInputError


def main(config_file: str = "config.yaml"):
    """Main function for the Huey project.

    Parameters
    ----------
    config_file: str, optional
        Path to the configuration YAML file. Defaults to ``"config.yaml"``.
    """
    try:
        # Load configuration
        config = load_config(config_file)
        # Set up logging with configuration
        setup_logging(config)
        logging.info("Huey application started.")

        # Example usage
        a, b = 5, 7
        validate_input(a, int)
        validate_input(b, int)
        result = calculate_sum(a, b)
        logging.info(f"The result of calculate_sum({a}, {b}) is {result}.")
        print(f"The sum of {a} and {b} is {result}.")

    except InvalidInputError as e:
        logging.error(f"Invalid input: {e}")
        print(f"Invalid input: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
