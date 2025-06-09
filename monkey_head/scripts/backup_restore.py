# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import os
from ..utils.logger import get_logger
import subprocess
from ..core.system_checks import check_error

logger = get_logger(__name__)


def backup_config():
    logger.info("Backing up Configurations...")
    backup_dir = os.path.expanduser("~/Backup/repo/config")
    os.makedirs(backup_dir, exist_ok=True)
    backup = subprocess.run(
        ["cp", "-r", os.path.expanduser("~/Source/repo/config"), backup_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(restore, "Restore Configurations")
