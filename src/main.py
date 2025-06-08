# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import logging
from flask import Flask, jsonify
from core.system_checks import system_check, ensure_admin
from modules.updates import update_system, update_python_packages
from core.installations import (
    install_common_tools,
    install_additional_tools,
    install_optional_tools,
)
from services.environment_setup import (
    clone_repository,
    setup_python_env,
    configure_git,
    create_directories,
    update_env_variables,
)
from services.container_management import (
    manage_containers,
    manage_volumes,
    deploy_kubernetes,
    kubernetes_management,
)
from scripts.backup_restore import backup_config, restore_config

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify(status="healthy"), 200


@app.route("/ready", methods=["GET"])
def readiness_check():
    return jsonify(status="ready"), 200


def main() -> None:
    """Run full setup and start the health service."""
    ensure_admin()
    system_check()
    update_system()
    install_common_tools()
    install_additional_tools()
    install_optional_tools()
    clone_repository()
    setup_python_env()
    configure_git()
    create_directories()
    update_env_variables()
    update_python_packages()
    manage_containers()
    manage_volumes()
    deploy_kubernetes()
    kubernetes_management()
    backup_config()
    restore_config()

    app.run(host="0.0.0.0", port=4488)


if __name__ == "__main__":
    main()
