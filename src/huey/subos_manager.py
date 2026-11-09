"""Subset of SubOS management helpers used in tests."""

from __future__ import annotations

import re
import subprocess

from huey.os.core.privileged_operations import authorize_privileged_operation

try:
    import pwd
except ImportError:  # pragma: no cover - Windows fallback for tests

    class _PwdModule:
        @staticmethod
        def getpwnam(_user: str):
            raise KeyError(_user)

    pwd = _PwdModule()  # type: ignore[assignment]


def update_system(*, confirmed: bool = False, actor_role: str | None = None) -> None:
    authorize_privileged_operation(
        "host.package_update", confirmed=confirmed, actor_role=actor_role
    )
    subprocess.run(
        ["apt-get", "update"],
        capture_output=True,
        check=True,
        shell=False,
        timeout=1800,
    )
    subprocess.run(
        ["apt-get", "upgrade", "-y"],
        capture_output=True,
        check=True,
        shell=False,
        timeout=1800,
    )


def create_user(
    username: str, *, confirmed: bool = False, actor_role: str | None = None
) -> None:
    authorize_privileged_operation(
        "host.user_create", confirmed=confirmed, actor_role=actor_role
    )
    if not isinstance(username, str) or not re.fullmatch(
        r"[a-z_][a-z0-9_-]{0,31}\$?", username
    ):
        raise ValueError("Invalid username")
    try:
        pwd.getpwnam(username)
        return
    except KeyError:
        pass

    subprocess.run(
        ["useradd", "-m", username],
        capture_output=True,
        check=True,
        shell=False,
        timeout=30,
    )


__all__ = ["create_user", "update_system"]
