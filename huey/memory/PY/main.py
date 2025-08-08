# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Main entry point for Monkey Head server."""

from monkey_head.utils.logger import get_logger
from flask import Flask, jsonify
import argparse
try:
    from pygpt_net import __version__ as pygpt_version
except Exception:  # pragma: no cover - optional dependency
    import os
    import sys

    fallback = os.path.join(os.path.dirname(__file__), "..", "repo", "pygpt-MHP", "src")
    if fallback not in sys.path:
        sys.path.append(fallback)
    try:  # pragma: no cover - best effort
        from pygpt_net import __version__ as pygpt_version
    except Exception:
        pygpt_version = "unknown"
from .core.system_checks import system_check, ensure_admin, check_python_version
from .modules.updates import update_system, update_python_packages
from .core.installations import (
    install_common_tools,
    install_additional_tools,
    install_optional_tools,
)
from .services.environment_setup import (
    clone_repository,
    setup_python_env,
    configure_git,
    create_directories,
    update_env_variables,
)
from .services.container_management import (
    manage_containers,
    manage_volumes,
    deploy_kubernetes,
    kubernetes_management,
)
from .scripts.backup_restore import backup_config, restore_config
from .logging_setup import configure_logging

app = Flask(__name__)

# Configure centralized logging
configure_logging()
logger = get_logger(__name__)


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify(status="healthy"), 200


@app.route("/ready", methods=["GET"])
def readiness_check():
    return jsonify(status="ready"), 200


@app.route("/version", methods=["GET"])
def version_info() -> tuple:
    """Return application version."""
    return jsonify(version=pygpt_version), 200


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Start Monkey Head server")
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip environment setup steps",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host interface to bind",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4488,
        help="Port to listen on",
    )
    return parser.parse_args(args)


def run_setup() -> None:
    """Run full environment setup."""
    ensure_admin()
    check_python_version()
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


def main() -> None:
    """Run setup tasks and start the health service."""
    args = parse_args()
    if not args.skip_setup:
        run_setup()
    logger.info("Starting server on %s:%s", args.host, args.port)
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
