# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Environment Setup Git module (tests)

from unittest.mock import patch

import pytest

from monkey_head.services.environment_setup import (
    checkout_branch,
    clone_repository,
    commit_and_push,
    pull_latest,
)


def test_checkout_branch():
    with patch("monkey_head.services.environment_setup.run_command") as run:
        checkout_branch("dev", dest="/tmp/repo")
        run.assert_any_call(["git", "fetch"], cwd="/tmp/repo")
        run.assert_any_call(["git", "checkout", "dev"], cwd="/tmp/repo")


def test_pull_latest():
    with patch("monkey_head.services.environment_setup.run_command") as run:
        pull_latest(dest="/tmp/repo")
        run.assert_called_once_with(["git", "pull", "--ff-only"], cwd="/tmp/repo")


def test_commit_and_push():
    with patch("monkey_head.services.environment_setup.run_command") as run:
        commit_and_push("msg", dest="/tmp/repo", remote="origin", branch="main")
        run.assert_any_call(["git", "add", "."], cwd="/tmp/repo")
        run.assert_any_call(["git", "commit", "-m", "msg"], cwd="/tmp/repo")
        run.assert_any_call(["git", "push", "origin", "main"], cwd="/tmp/repo")


def test_clone_repository_fallback():
    """Clone should fall back to existing repo on failure."""
    with (
        patch(
            "monkey_head.services.environment_setup.run_command",
            side_effect=RuntimeError("git error"),
        ) as run,
        patch(
            "monkey_head.services.environment_setup.os.path.isdir",
            side_effect=lambda p: p.endswith(".git"),
        ) as isdir,
        patch("monkey_head.services.environment_setup.logger.warning") as warn,
        patch("monkey_head.services.environment_setup.os.makedirs"),
    ):
        clone_repository(dest="/tmp/repo")
        run.assert_called_once()
        isdir.assert_called()
        warn.assert_called_once()


def test_clone_repository_error():
    """Clone should raise if repo absent on failure."""
    with (
        patch(
            "monkey_head.services.environment_setup.run_command",
            side_effect=RuntimeError("git error"),
        ) as run,
        patch(
            "monkey_head.services.environment_setup.os.path.isdir",
            return_value=False,
        ),
        patch("monkey_head.services.environment_setup.os.makedirs"),
    ):
        with pytest.raises(RuntimeError):
            clone_repository(dest="/tmp/repo")
        run.assert_called_once()
