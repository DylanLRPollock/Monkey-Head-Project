# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
from .logger import get_logger

logger = get_logger(__name__)
import subprocess


def check_linux_service(service_name):
    """
    Checks the status of a Linux service.

    Args:
        service_name (str): The name of the service to check.

    Returns:
        str: The status of the service ('active', 'inactive', 'failed', etc.).

    Raises:
        OSError: If there is an error checking the service status.
    """
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        status = result.stdout.decode("utf-8").strip()
        if status == "active":
            logger.debug(f"Service {service_name} is active")
            return "active"
        elif status == "inactive":
            logger.debug(f"Service {service_name} is inactive")
            return "inactive"
        elif status == "failed":
            logger.debug(f"Service {service_name} has failed")
            return "failed"
        else:
            logger.debug(f"Service {service_name} status unknown: {status}")
            return "unknown"
    except OSError as e:
        logger.exception("Error checking linux service")
        raise OSError(f"Error checking service '{service_name}': {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check the status of a Linux service.")
    parser.add_argument("service_name", help="The name of the service to check.")
    args = parser.parse_args()

    try:
        status = check_linux_service(args.service_name)
        message = f"Service '{args.service_name}' is {status}."
        print(message)
        logger.info(message)
    except Exception as e:
        logger.exception("Error checking linux service from CLI")
        print(f"Error: {e}")
