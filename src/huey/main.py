"""Lightweight shim replicating :mod:`monkey_head.main` interfaces.

The historical implementation lived under ``huey/memory/PY/main.py`` and
pulled in numerous heavy runtime dependencies.  Tests and downstream
consumers primarily rely on the public functions and objects exported by
that module rather than its side effects, so this shim provides a
self-contained version that reuses the same signatures while remaining
importable in minimal environments.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Tuple

from monkey_head.pytorch_tools import device_summary

@dataclass
class _Route:
    path: str
    methods: Tuple[str, ...]
    handler: Callable[..., Any]


@dataclass
class _StubApp:
    """Tiny stand-in for Flask's :class:`~flask.Flask` application.

    The stub records routes registered via :meth:`route` and offers a
    simple :meth:`run` method whose behaviour can be monkeypatched by
    tests.  This keeps the public surface compatible without requiring
    the real Flask dependency.
    """

    routes: Dict[Tuple[str, Tuple[str, ...]], _Route] = field(default_factory=dict)

    def route(self, path: str, *, methods: Iterable[str] | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        allowed = tuple(methods) if methods is not None else tuple()

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes[(path, allowed)] = _Route(path, allowed, func)
            return func

        return decorator

    def run(self, host: str, port: int) -> Dict[str, Any]:
        # Mirror Flask's return value shape loosely; tests typically
        # monkeypatch this method, so the body is intentionally simple.
        return {"host": host, "port": port}


def jsonify(**payload: Any) -> Dict[str, Any]:
    """Return a JSON-serialisable payload.

    The real Flask helper builds a response object; for testing purposes,
    a plain dictionary is sufficient and easier to inspect.
    """

    return payload


app = _StubApp()


@app.route("/health", methods=["GET"])
def health_check() -> tuple[Dict[str, str], int]:
    return {"status": "healthy"}, 200


@app.route("/ready", methods=["GET"])
def readiness_check() -> tuple[Dict[str, str], int]:
    return {"status": "ready"}, 200


@app.route("/version", methods=["GET"])
def version_info(version: str = "unknown") -> tuple[Dict[str, str], int]:
    return {"version": version}, 200


@app.route("/pytorch/info", methods=["GET"])
def pytorch_info() -> tuple[Dict[str, Any], int]:
    return device_summary(), 200


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the Monkey Head server."""

    parser = argparse.ArgumentParser(description="Start Monkey Head server")
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip environment setup steps",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
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
    """Placeholder for the historical setup routine."""

    return None


def main() -> None:
    """Run setup tasks and start the minimal health service."""

    args = parse_args()
    if not args.skip_setup:
        run_setup()
    app.run(host=args.host, port=args.port)


__all__ = [
    "app",
    "health_check",
    "readiness_check",
    "version_info",
    "pytorch_info",
    "parse_args",
    "run_setup",
    "main",
    "jsonify",
]
