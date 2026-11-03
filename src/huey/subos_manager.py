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
    subprocess.run(["apt-get", "update"], capture_output=True)
    subprocess.run(
        ["apt-get", "upgrade", "-y"],
        capture_output=True,
    )


def create_user(username: str) -> None:
    try:
        pwd.getpwnam(username)
        return
    except KeyError:
        pass

    subprocess.run(
        ["useradd", "-m", username],
        capture_output=True,
    )


__all__ = ["create_user", "update_system"]
