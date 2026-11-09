"""Launch upstream PyGPT and publish a HueyOS MCP connector configuration.

The real PyGPT application is installed separately; this module never treats
the lightweight vendored PyHuey compatibility package as the upstream GUI.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from huey.integrations.pygpt_mcp import DEFAULT_API_PORT, serve


def pygpt_executable() -> str | None:
    """Resolve the upstream PyGPT executable without invoking a shell."""

    override = os.environ.get("PYGPT_EXECUTABLE")
    if override:
        return shutil.which(override)
    return shutil.which("pygpt")


def connector_config() -> dict[str, object]:
    """Generate a standard MCP connector import for a local PyGPT profile."""

    return {
        "mcpServers": {
            "hueyos": {
                "command": sys.executable,
                "args": ["-m", "huey.integrations.pygpt_mcp"],
                "env": {"HUEY_API_PORT": os.getenv("HUEY_API_PORT", DEFAULT_API_PORT)},
            }
        }
    }


def doctor() -> dict[str, object]:
    """Report actionable installation status without importing PySide6."""

    executable = pygpt_executable()
    try:
        package_version = importlib.metadata.version("pygpt-net")
    except importlib.metadata.PackageNotFoundError:
        package_version = None
    return {
        "upstream_executable": executable,
        "pygpt_in_current_environment": package_version,
        "gui_available": executable is not None,
        "hueyos_python": sys.version.split()[0],
        "mcp_server": "huey.integrations.pygpt_mcp",
        "mcp_transport": "stdio",
        "huey_api_port": os.getenv("HUEY_API_PORT", DEFAULT_API_PORT),
    }


def launch_gui(*, workdir: Path | None = None) -> int:
    """Execute the genuine upstream GUI; do not start a simulated PyHuey."""

    executable = pygpt_executable()
    if executable is None:
        print(
            "PyGPT executable not found. Install pygpt-net==2.9.1 into a "
            "Python 3.13 environment and ensure 'pygpt' is on PATH, or "
            "set PYGPT_EXECUTABLE to its absolute path.",
            file=sys.stderr,
        )
        return 2

    command = [executable]
    env = os.environ.copy()
    if workdir is not None:
        env["PYGPT_WORKDIR"] = str(workdir.expanduser().resolve())
    try:
        return subprocess.run(command, check=False, shell=False, env=env).returncode
    except OSError as exc:
        print(f"Unable to start PyGPT: {exc}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    """CLI for upstream GUI, diagnostics and the MCP stdio process."""

    parser = argparse.ArgumentParser(
        description="Upstream PyGPT operator interface for HueyOS"
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    gui = subcommands.add_parser("gui", help="Start the real PyGPT desktop GUI")
    gui.add_argument(
        "--workdir",
        type=Path,
        help="Optional PyGPT profile directory (not the HueyOS data directory)",
    )
    subcommands.add_parser("mcp", help="Serve read-only Huey tools over MCP stdio")
    subcommands.add_parser("connector", help="Print the PyGPT MCP import JSON")
    subcommands.add_parser("doctor", help="Report PyGPT runtime availability")

    args = parser.parse_args(argv)
    if args.command == "gui":
        return launch_gui(workdir=args.workdir)
    if args.command == "mcp":
        serve()
        return 0
    if args.command == "connector":
        print(json.dumps(connector_config(), indent=2))
        return 0
    if args.command == "doctor":
        print(json.dumps(doctor(), indent=2))
        return 0
    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
