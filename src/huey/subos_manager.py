"""Subset of SubOS management helpers used in tests."""

from __future__ import annotations

import subprocess

try:
    import pwd
except ImportError:  # pragma: no cover - Windows fallback for tests
    class _PwdModule:
        @staticmethod
        def getpwnam(_user: str):
            raise KeyError(_user)

    pwd = _PwdModule()  # type: ignore[assignment]


def update_system() -> None:
    subprocess.run(
        ["apt-get", "update"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
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
