"""CLI launcher for the read-only Command Center backend."""

from __future__ import annotations

import argparse
import threading
import webbrowser


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


def open_browser(url: str) -> None:
    """Open the default browser to the local Command Center URL."""

    webbrowser.open(url)


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
    url = f"http://{args.host}:{args.port}/command-center/meta"
    if args.open_browser:
        threading.Timer(1.0, open_browser, args=(url,)).start()
    run_server(args.host, args.port, reload=args.reload)
    return 0


__all__ = ["main", "open_browser", "parse_args", "run_server"]
