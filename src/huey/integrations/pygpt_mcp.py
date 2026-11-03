"""Read-only MCP stdio bridge from upstream PyGPT to HueyOS.

This is deliberately independent of Qt, PyGPT internals and the legacy
PyHuey connector tree. The MCP process never dispatches arbitrary commands.
"""

from __future__ import annotations

import http.client
import importlib.metadata
import json
import os
import shutil
import sys
from collections.abc import Callable
from typing import Any, TextIO

_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}
_DEFAULT_PROTOCOL = "2025-06-18"

_TOOLS: list[dict[str, object]] = [
    {
        "name": "huey_project",
        "description": "Read HueyOS identity and installed package version.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "huey_health",
        "description": "Check the local HueyOS API /healthz endpoint (read-only).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "huey_diagnostics",
        "description": "Check whether FFmpeg and ffprobe executables are available.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "huey_permissions",
        "description": "Describe the actions deliberately not exposed to PyGPT.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
]


def project_info() -> dict[str, object]:
    """Report package identity without importing the running robot."""

    try:
        version = importlib.metadata.version("hueyos")
    except importlib.metadata.PackageNotFoundError:
        version = None
    return {
        "project": "Monkey-Head-Project",
        "runtime": "HueyOS",
        "package_version": version,
        "pygpt_role": "operator-interface",
        "bridge": "mcp-stdio-read-only",
    }


def health_info() -> dict[str, object]:
    """Connect only to IPv4 loopback, never to an operator-supplied URL."""

    raw_port = os.environ.get("HUEY_API_PORT", "8000")
    try:
        port = int(raw_port)
    except ValueError:
        return {"connected": False, "error": "Invalid HUEY_API_PORT"}
    if not 1 <= port <= 65535:
        return {"connected": False, "error": "Invalid HUEY_API_PORT"}
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        conn.request("GET", "/healthz")
        response = conn.getresponse()
        data = response.read(4096)
        if response.status != 200:
            return {"connected": False, "status_code": response.status}
        payload = json.loads(data)
        if not isinstance(payload, dict):
            return {"connected": False, "error": "Unexpected API response"}
        return {
            "connected": True,
            "status": payload.get("status"),
            "service": payload.get("service"),
        }
    except (OSError, http.client.HTTPException, ValueError) as exc:
        return {"connected": False, "error": type(exc).__name__}
    finally:
        conn.close()


def diagnostics() -> dict[str, object]:
    """Inspect tool availability without invoking external processes."""

    return {
        "ffmpeg_available": shutil.which("ffmpeg") is not None,
        "ffprobe_available": shutil.which("ffprobe") is not None,
    }


def permissions() -> dict[str, object]:
    """Document the narrow permissions of this MCP bridge."""

    return {
        "mode": "read-only",
        "allowed": [item["name"] for item in _TOOLS],
        "not_exposed": [
            "hardware_actuation",
            "power_management",
            "governance_mutation",
            "memory_mutation",
            "filesystem_mutation",
            "shell_execution",
            "task_submission",
            "network_configuration",
        ],
        "note": (
            "These restrictions apply only to the HueyOS MCP bridge; "
            "configure other PyGPT plugins separately."
        ),
    }


_ACTIONS: dict[str, Callable[[], dict[str, object]]] = {
    "huey_project": project_info,
    "huey_health": health_info,
    "huey_diagnostics": diagnostics,
    "huey_permissions": permissions,
}


def _error(request_id: object, code: int, message: str) -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def dispatch(request: object) -> dict[str, object] | None:
    """Dispatch one JSON-RPC request; notifications produce no response."""

    if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
        return _error(None, -32600, "Invalid Request")

    if "id" not in request:
        return None
    request_id = request["id"]
    if (
        isinstance(request_id, bool)
        or not isinstance(request_id, (str, int))
        and request_id is not None
    ):
        return _error(None, -32600, "Invalid Request")

    method = request.get("method")
    params = request.get("params", {})
    if not isinstance(method, str):
        return _error(request_id, -32600, "Invalid Request")
    if not isinstance(params, dict):
        return _error(request_id, -32602, "Invalid params")

    result: dict[str, object]
    if method == "initialize":
        version = params.get("protocolVersion")
        if version not in _PROTOCOL_VERSIONS:
            version = _DEFAULT_PROTOCOL
        result = {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "hueyos", "version": "1.0.0"},
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": _TOOLS}
    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        if not isinstance(name, str) or name not in _ACTIONS:
            return _error(request_id, -32602, "Unknown tool")
        if not isinstance(args, dict) or args:
            return _error(request_id, -32602, "Tool takes no arguments")
        try:
            payload = _ACTIONS[name]()
        except Exception:
            result = {
                "isError": True,
                "content": [{"type": "text", "text": "Huey tool failed"}],
            }
        else:
            result = {
                "content": [
                    {"type": "text", "text": json.dumps(payload, sort_keys=True)}
                ]
            }
    else:
        return _error(request_id, -32601, "Method not found")

    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def serve(
    input_stream: TextIO | None = None, output_stream: TextIO | None = None
) -> None:
    """Serve newline-delimited MCP messages over stdio until EOF."""

    source = sys.stdin if input_stream is None else input_stream
    target = sys.stdout if output_stream is None else output_stream
    for line in source:
        try:
            request: Any = json.loads(line)
        except json.JSONDecodeError:
            response = _error(None, -32700, "Parse error")
        else:
            response = dispatch(request)
        if response is not None:
            target.write(json.dumps(response, separators=(",", ":")) + "\n")
            target.flush()


def main() -> int:
    serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
