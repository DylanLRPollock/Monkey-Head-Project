"""WSGI entry point for lightweight runtime deployment."""

from __future__ import annotations

import json

from .main import build_application_context

_CONTEXT = build_application_context()


def application(environ: dict[str, object], start_response: object) -> list[bytes]:
    path = str(environ.get("PATH_INFO", "/"))
    if path in {"/", "/health", "/healthz"}:
        status = "200 OK"
        payload = _CONTEXT.kernel.health_report()
    elif path == "/kernel":
        status = "200 OK"
        payload = _CONTEXT.kernel.snapshot()
    elif path == "/routes":
        status = "200 OK"
        payload = {"routes": _CONTEXT.api_bridge.describe()}
    else:
        status = "404 Not Found"
        payload = {"error": "not found", "path": path}

    body = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


app = application

__all__ = ["app", "application"]
