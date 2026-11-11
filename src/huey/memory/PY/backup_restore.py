# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Backup Restore module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.09.2025
# ==================================================
import os
import subprocess

from huey.memory.PY.logger import get_logger
from huey.os.core.system_checks import check_error

logger = get_logger(__name__)


def backup_config():
    logger.info("Backing up Configurations...")
    backup_dir = os.path.expanduser("~/Backup/repo/config")
    os.makedirs(backup_dir, exist_ok=True)
    backup = subprocess.run(
        ["cp", "-r", os.path.expanduser("~/Source/repo/config"), backup_dir],
        capture_output=True,
    )
    check_error(backup, "Backup Configurations")


def restore_config():
    logger.info("Restoring Configurations...")
    restore = subprocess.run(
        [
            "cp",
            "-r",
            os.path.expanduser("~/Backup/repo/config"),
            os.path.expanduser("~/Source/repo/config"),
        ],
        capture_output=True,
    )
    check_error(restore, "Restore Configurations")
