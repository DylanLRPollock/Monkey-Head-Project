# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Subos Manager module (tests)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.09.2025
# ==================================================
import types
from unittest.mock import patch

import pytest

from huey.os import subos_manager


class R:
    def __init__(self):
        self.returncode = 0


def test_update_system_runs_commands():
    with patch("subprocess.run", return_value=R()) as mock_run:
        subos_manager.update_system(confirmed=True, actor_role="admin")
        mock_run.assert_any_call(
            ["apt-get", "update"],
            capture_output=True,
            check=True,
            shell=False,
            timeout=1800,
        )
        mock_run.assert_any_call(
            ["apt-get", "upgrade", "-y"],
            capture_output=True,
            check=True,
            shell=False,
            timeout=1800,
        )


def test_create_user_skips_existing():
    with (
        patch("pwd.getpwnam", return_value=types.SimpleNamespace()),
        patch("subprocess.run") as mock_run,
    ):
        subos_manager.create_user("nobody", confirmed=True, actor_role="admin")
        mock_run.assert_not_called()


def test_create_user_adds_new():
    with (
        patch("pwd.getpwnam", side_effect=KeyError),
        patch("subprocess.run", return_value=R()) as mock_run,
    ):
        subos_manager.create_user("subos", confirmed=True, actor_role="admin")
        mock_run.assert_called_with(
            ["useradd", "-m", "subos"],
            capture_output=True,
            check=True,
            shell=False,
            timeout=30,
        )


def test_host_mutations_deny_without_confirmation_before_process_creation():
    with patch("subprocess.run", side_effect=AssertionError("spawned")) as mock_run:
        with pytest.raises(PermissionError):
            subos_manager.update_system()
        with pytest.raises(PermissionError):
            subos_manager.create_user("huey")
    mock_run.assert_not_called()


def test_create_user_rejects_invalid_name_before_subprocess():
    with (
        patch("subprocess.run", side_effect=AssertionError("spawned")) as mock_run,
        pytest.raises(ValueError, match="Invalid username"),
    ):
        subos_manager.create_user("../huey", confirmed=True, actor_role="admin")
    mock_run.assert_not_called()
