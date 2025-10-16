# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Environment Setup module (src/monkey_head/services)

"""Minimal project environment management helpers used in tests."""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Sequence

logger = logging.getLogger(__name__)

DEFAULT_REPO_URL = "https://github.com/DylanLRPollock/Monkey-Head-Project.git"


def run_command(command: Sequence[str], *, cwd: str | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    """Run ``command`` via :func:`subprocess.run` and return the completed process."""

    return subprocess.run(command, cwd=cwd, check=check, text=True)


def _expand(path: str) -> str:
    return os.path.expanduser(path)


def clone_repository(repo_url: str = DEFAULT_REPO_URL, dest: str = "~/Source/repo") -> None:
    """Clone ``repo_url`` into ``dest`` creating parent directories as required."""

    dest_path = _expand(dest)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    try:
        run_command(["git", "clone", repo_url, dest_path], check=True)
    except Exception as exc:  # pragma: no cover - error path exercised in tests
        git_dir = os.path.join(dest_path, ".git")
        if os.path.isdir(git_dir):
            logger.warning("Clone failed (%s). Using existing repository at %s", exc, dest_path)
        else:
            raise


def setup_python_env(dest: str = "~/Source/repo") -> None:
    """Create a virtual environment inside ``dest`` and install requirements."""

    dest_path = _expand(dest)
    venv_path = os.path.join(dest_path, "venv")
    if not os.path.isdir(venv_path):
        run_command(["python3", "-m", "venv", venv_path], check=True)

    pip_exe = os.path.join(venv_path, "bin", "pip")
    run_command([pip_exe, "install", "--upgrade", "pip"], cwd=dest_path, check=True)
    run_command([pip_exe, "install", "-r", "requirements.txt"], cwd=dest_path, check=True)


def configure_git(name: str = "Your Name", email: str = "your.email@example.com") -> None:
    """Set the global git username and email values."""

    run_command(["git", "config", "--global", "user.name", name], check=True)
    run_command(["git", "config", "--global", "user.email", email], check=True)


def checkout_branch(branch: str, dest: str = "~/Source/repo") -> None:
    """Fetch the latest refs and checkout ``branch`` in ``dest``."""

    dest_path = _expand(dest)
    run_command(["git", "fetch"], cwd=dest_path)
    run_command(["git", "checkout", branch], cwd=dest_path)


def pull_latest(dest: str = "~/Source/repo") -> None:
    """Pull the latest commits using ``--ff-only`` to avoid merge commits."""

    dest_path = _expand(dest)
    run_command(["git", "pull", "--ff-only"], cwd=dest_path)


def commit_and_push(message: str, dest: str = "~/Source/repo", remote: str = "origin", branch: str = "main") -> None:
    """Commit staged changes with ``message`` and push to ``remote`` ``branch``."""

    dest_path = _expand(dest)
    run_command(["git", "add", "."], cwd=dest_path)
    run_command(["git", "commit", "-m", message], cwd=dest_path)
    run_command(["git", "push", remote, branch], cwd=dest_path)


__all__ = [
    "clone_repository",
    "setup_python_env",
    "configure_git",
    "checkout_branch",
    "pull_latest",
    "commit_and_push",
    "run_command",
]
