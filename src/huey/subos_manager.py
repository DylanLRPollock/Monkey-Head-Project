"""Subset of SubOS management helpers used in tests."""

from __future__ import annotations

import pwd
import subprocess


def update_system() -> None:
    subprocess.run(["apt-get", "update"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(
        ["apt-get", "upgrade", "-y"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def create_user(username: str) -> None:
    try:
        pwd.getpwnam(username)
        return
    except KeyError:
        pass

    subprocess.run(
        ["useradd", "-m", username],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


__all__ = ["update_system", "create_user"]
