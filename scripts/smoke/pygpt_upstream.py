#!/usr/bin/env python3
"""Exercise the pinned GUI and its actual MCP importer/worker against HueyOS.

Run with the PyGPT venv's Python under Xvfb; HUEY_PYTHON names the separate
HueyOS venv's Python. This test never loads PyGPT modules into HueyOS.
"""

from __future__ import annotations

import asyncio
import contextlib
import importlib.metadata
import json
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace

from pygpt_net.core.connectors.connectors import Connectors
from pygpt_net.plugin.mcp.worker import Worker


def wait_for_health(port: int, process: subprocess.Popen) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Huey API exited with {process.returncode}")
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/healthz", timeout=1
            ) as response:
                if json.load(response) == {"status": "ok", "service": "hueyos"}:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.5)
    raise RuntimeError("Huey API did not become healthy")


def wait_for_window(process: subprocess.Popen, log: Path) -> None:
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"PyGPT launcher exited ({process.returncode}):\n{log.read_text()}"
            )
        windows = subprocess.check_output(["xwininfo", "-root", "-tree"], text=True)
        if re.search(r'"PyGPT 2\.9\.1 \| build ', windows):
            return
        time.sleep(1)
    raise RuntimeError(f"PyGPT main window did not appear:\n{log.read_text()}")


async def check_connector(connector: dict) -> None:
    worker = Worker()
    worker.plugin = SimpleNamespace(get_stdio_cwd=lambda server: None)
    async with worker._open_session(
        connector["server_address"], connector["transport"], connector
    ) as session:
        tools = await session.list_tools()
        names = {tool.name for tool in tools.tools}
        assert names == {
            "huey_project",
            "huey_health",
            "huey_diagnostics",
            "huey_connections",
            "huey_permissions",
        }
        result = await session.call_tool("huey_health", arguments={})
        assert not result.isError
        payload = json.loads(result.content[0].text)
        assert payload == {"connected": True, "status": "ok", "service": "hueyos"}


def main() -> None:
    assert importlib.metadata.version("pygpt-net") == "2.9.1"
    huey_python = os.path.abspath(os.environ["HUEY_PYTHON"])
    pygpt = str(Path(sys.executable).parent / "pygpt")
    assert Path(huey_python) != Path(sys.executable)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryDirectory(
        prefix="huey-pygpt-smoke-", ignore_cleanup_errors=True
    ) as tmp:
        root = Path(tmp)
        env = {
            key: os.environ[key]
            for key in ("PATH", "DISPLAY", "XAUTHORITY", "LANG", "LC_ALL")
            if key in os.environ
        }
        env.update(
            HOME=str(root),
            HUEY_API_PORT=str(port),
            PYGPT_EXECUTABLE=pygpt,
            QTWEBENGINE_DISABLE_SANDBOX="1",
        )
        os.environ.clear()
        os.environ.update(env)
        with (
            (root / "api.log").open("w+") as api_log,
            (root / "gui.log").open("w+") as gui_log,
        ):
            api = subprocess.Popen(
                [
                    huey_python,
                    "-m",
                    "uvicorn",
                    "huey.api:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                env=env,
                stdout=api_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            gui = None
            try:
                wait_for_health(port, api)
                config = subprocess.check_output(
                    [huey_python, "-m", "huey.integrations.pygpt_cli", "connector"],
                    env=env,
                )
                config_path = root / "connector.json"
                config_path.write_bytes(config)
                connectors = Connectors().import_local(str(config_path), persist=False)
                assert len(connectors) == 1
                assert connectors[0]["active"] is False
                gui = subprocess.Popen(
                    [
                        huey_python,
                        "-m",
                        "huey.integrations.pygpt_cli",
                        "gui",
                        "--workdir",
                        str(root / "profile"),
                    ],
                    env=env,
                    stdout=gui_log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                wait_for_window(gui, root / "gui.log")
                asyncio.run(check_connector(connectors[0]))
                print(
                    "PyGPT GUI, connector import and read-only Huey health call succeeded."
                )
            except Exception:
                api_log.flush()
                gui_log.flush()
                print(
                    "Huey API log:\n" + (root / "api.log").read_text(), file=sys.stderr
                )
                print("PyGPT log:\n" + (root / "gui.log").read_text(), file=sys.stderr)
                raise
            finally:
                for process in (gui, api):
                    if process is not None:
                        if process.poll() is None:
                            with contextlib.suppress(ProcessLookupError):
                                os.killpg(process.pid, signal.SIGTERM)
                            with contextlib.suppress(subprocess.TimeoutExpired):
                                process.wait(timeout=10)
                        # The GUI can leave child processes behind after its
                        # launcher exits. Kill the original process group again
                        # before the temporary profile is removed.
                        with contextlib.suppress(ProcessLookupError):
                            os.killpg(process.pid, signal.SIGKILL)
                        process.wait()


if __name__ == "__main__":
    main()
