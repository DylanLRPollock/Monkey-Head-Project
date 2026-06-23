"""CLI launcher for the read-only Command Center backend."""

from __future__ import annotations

import argparse
import os
import threading
import webbrowser
from pathlib import Path

from huey.apps.command_center.static_config import command_center_frontend_url


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse Command Center CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Run the HueyOS Command Center backend"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1996)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--open", action="store_true", dest="open_browser")
    return parser.parse_args(argv)


def _project_root() -> Path | None:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    cwd = Path.cwd()
    if (cwd / "pyproject.toml").is_file():
        return cwd
    return None


def local_frontend_path(project_root: str | Path | None = None) -> Path | None:
    """Return the bundled Command Center frontend when it exists locally."""

    root = Path(project_root) if project_root is not None else _project_root()
    if root is None:
        return None
    candidate = root / "integrations" / "command-center" / "dist" / "index.html"
    if candidate.is_file():
        return candidate
    return None


def resolve_frontend_url(project_root: str | Path | None = None) -> str:
    """Return the best browser target for the local Command Center UI."""

    configured = os.environ.get("HUEY_COMMAND_CENTER_FRONTEND")
    if configured:
        return configured
    local_frontend = local_frontend_path(project_root)
    if local_frontend is not None:
        return local_frontend.resolve().as_uri()
    return command_center_frontend_url()


def open_browser(url: str) -> None:
    """Open the default browser to the requested Command Center URL."""

    webbrowser.open(url)


def open_command_center() -> str:
    """Open the best available Command Center frontend and return its URL."""

    url = resolve_frontend_url()
    open_browser(url)
    return url


def run_server(host: str, port: int, reload: bool = False) -> None:
    """Run uvicorn with the Command Center backend."""

    import uvicorn

    uvicorn.run(
        "huey.apps.command_center.server:app",
        host=host,
        port=port,
        reload=reload,
    )


def main(argv: list[str] | None = None) -> int:
    """Command entry point."""

    args = parse_args(argv)
    if args.open_browser:
        threading.Timer(1.0, open_command_center).start()
    run_server(args.host, args.port, reload=args.reload)
    return 0


__all__ = [
    "local_frontend_path",
    "main",
    "open_browser",
    "open_command_center",
    "parse_args",
    "resolve_frontend_url",
    "run_server",
]
