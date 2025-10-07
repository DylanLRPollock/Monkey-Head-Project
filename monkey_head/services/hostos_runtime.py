"""HostOS runtime orchestration utilities."""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import shutil
import signal
import subprocess
import time
from typing import List, Optional

import uvicorn
from src.huey.api import app as huey_app

logger = logging.getLogger("hostos-runtime")


def _spawn_process(cmd: List[str], *, env: Optional[dict] = None) -> Optional[subprocess.Popen]:
    """Spawn *cmd* if the executable is available."""

    if shutil.which(cmd[0]) is None:
        logger.warning("Unable to start %s because it is not installed.", cmd[0])
        return None

    logger.info("Launching %s", " ".join(cmd))
    return subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


async def _run_dashboard(host: str, port: int) -> None:
    """Start the Huey API using uvicorn."""

    config = uvicorn.Config(huey_app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def launch_hostos(*, vnc_port: int = 5901, dashboard_port: int = 8000, display: str = ":0") -> None:
    """Launch the HostOS graphical environment and dashboard."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    processes: List[subprocess.Popen] = []
    env = os.environ.copy()
    env["DISPLAY"] = display

    try:
        xvfb = _spawn_process(
            ["Xvfb", display, "-screen", "0", "1920x1080x24", "-nolisten", "tcp"],
            env=env,
        )
        if xvfb:
            processes.append(xvfb)
            time.sleep(2)

        wm = _spawn_process(["openbox"], env=env)
        if wm:
            processes.append(wm)

        vnc = _spawn_process(
            ["x11vnc", "-display", display, "-forever", "-shared", "-nopw", "-rfbport", str(vnc_port)],
            env=env,
        )
        if vnc:
            processes.append(vnc)

        asyncio.run(_run_dashboard("0.0.0.0", dashboard_port))
    finally:
        for proc in processes:
            try:
                proc.send_signal(signal.SIGTERM)
            except Exception:
                continue


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the HostOS runtime services")
    parser.add_argument("--vnc-port", type=int, default=5901, help="VNC port to expose")
    parser.add_argument("--dashboard-port", type=int, default=8000, help="Huey dashboard port")
    parser.add_argument("--display", default=":0", help="X11 display to use for the virtual framebuffer")
    args = parser.parse_args()
    launch_hostos(vnc_port=args.vnc_port, dashboard_port=args.dashboard_port, display=args.display)


if __name__ == "__main__":
    main()
