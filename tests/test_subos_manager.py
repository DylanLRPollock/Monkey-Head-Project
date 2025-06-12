# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.09.2025
# ==================================================
import subprocess
from unittest.mock import patch
import types

from monkey_head import subos_manager


class R:
    def __init__(self):
        self.returncode = 0


def test_update_system_runs_commands():
    with patch("subprocess.run", return_value=R()) as mock_run:
        subos_manager.update_system()
        mock_run.assert_any_call(
            ["apt-get", "update"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        mock_run.assert_any_call(
            ["apt-get", "upgrade", "-y"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


def test_create_user_skips_existing():
    with patch("pwd.getpwnam", return_value=types.SimpleNamespace()), patch(
        "subprocess.run"
    ) as mock_run:
        subos_manager.create_user("nobody")
        mock_run.assert_not_called()


def test_create_user_adds_new():
    with patch("pwd.getpwnam", side_effect=KeyError), patch(
        "subprocess.run", return_value=R()
    ) as mock_run:
        subos_manager.create_user("subos")
        mock_run.assert_called_with(
            ["useradd", "-m", "subos"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
