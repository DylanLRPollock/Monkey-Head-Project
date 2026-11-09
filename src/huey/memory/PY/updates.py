# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Updates module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
import logging
import subprocess

from ..core.system_checks import check_error
from huey.os.core.privileged_operations import authorize_privileged_operation

logger = logging.getLogger(__name__)


def update_system(*, confirmed: bool = False, actor_role: str | None = None) -> bool:
    authorize_privileged_operation(
        "host.package_update", confirmed=confirmed, actor_role=actor_role
    )
    logger.info("Updating system...")
    update = subprocess.run(
        ["apt-get", "update"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        timeout=1800,
    )
    check_error(update, "System Update")

    upgrade = subprocess.run(
        ["apt-get", "upgrade", "-y"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        timeout=1800,
    )
    check_error(upgrade, "System Upgrade")
    return True


def update_python_packages(
    *, confirmed: bool = False, actor_role: str | None = None
) -> bool:
    authorize_privileged_operation(
        "project.update", confirmed=confirmed, actor_role=actor_role
    )
    logger.info("Updating Python Packages...")
    upgrade_pip = subprocess.run(
        ["pip", "install", "--upgrade", "pip"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        timeout=600,
    )
    check_error(upgrade_pip, "Pip Upgrade")

    update_packages = subprocess.run(
        ["pip", "install", "--upgrade", "-r", "requirements.txt"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        timeout=1800,
    )
    check_error(update_packages, "Update Python Packages")
    return True
