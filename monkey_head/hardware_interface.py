"""Unified hardware command interface across HostOS, SubOS and NanoOS."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Sequence


def _run(
    cmd: Sequence[str], cwd: str | Path | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def send_hostos(cmd: Sequence[str]) -> subprocess.CompletedProcess:
    """Send a command to the HostOS layer."""
    path = Path(os.environ.get("HOSTOS_PATH", "."))
    return _run(cmd, cwd=path)


def send_subos(cmd: Sequence[str]) -> subprocess.CompletedProcess:
    """Send a command to the SubOS layer."""
    path = Path(os.environ.get("SUBOS_PATH", "."))
    return _run(cmd, cwd=path)


def send_nanoos(cmd: Sequence[str]) -> subprocess.CompletedProcess:
    """Send a command to the NanoOS layer."""
    path = Path(os.environ.get("NANOOS_PATH", "."))
    return _run(cmd, cwd=path)
