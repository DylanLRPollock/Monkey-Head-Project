from monkey_head.services.environment_setup import (
    checkout_branch,
    pull_latest,
    commit_and_push,
)
from unittest.mock import patch


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
