"""Verify environment setup uses the expected commands and safe fallbacks."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from huey.memory.PY import environment_setup as setup


def test_clone_repository_creates_parent_and_runs_git_clone(monkeypatch, tmp_path):
    destination = tmp_path / "src" / "repo"
    calls = []
    monkeypatch.setattr(setup.os, "path", setup.os.path)
    monkeypatch.setattr(setup.os.path, "expanduser", lambda _path: str(destination))
    monkeypatch.setattr(
        setup.os, "makedirs", lambda *args, **kwargs: calls.append(args)
    )
    monkeypatch.setattr(
        setup, "run_command", lambda *args, **kwargs: calls.append((args, kwargs))
    )

    setup.clone_repository("https://example.test/repo.git", "~/src/repo")

    assert calls[0] == (str(destination.parent),)
    assert calls[1] == (
        (["git", "clone", "https://example.test/repo.git", str(destination)],),
        {"check": True},
    )


def test_clone_repository_reuses_existing_checkout_after_clone_error(monkeypatch):
    monkeypatch.setattr(setup.os.path, "expanduser", lambda _path: "/tmp/repo")
    monkeypatch.setattr(setup.os, "makedirs", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(setup.os.path, "isdir", lambda path: path == "/tmp/repo/.git")

    def fail_clone(*_args, **_kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(setup, "run_command", fail_clone)
    setup.clone_repository(dest="~/repo")


def test_clone_repository_propagates_when_no_existing_checkout(monkeypatch):
    monkeypatch.setattr(setup.os.path, "expanduser", lambda _path: "/tmp/new-repo")
    monkeypatch.setattr(setup.os, "makedirs", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(setup.os.path, "isdir", lambda _path: False)
    monkeypatch.setattr(
        setup,
        "run_command",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("clone failed")),
    )

    with pytest.raises(RuntimeError, match="clone failed"):
        setup.clone_repository(dest="~/new-repo")


def test_setup_python_env_creates_venv_and_installs_requirements(monkeypatch, tmp_path):
    repo = tmp_path / "project"
    monkeypatch.setattr(setup.os.path, "expanduser", lambda _path: str(repo))
    monkeypatch.setattr(setup.os.path, "isdir", lambda _path: False)
    commands = []
    monkeypatch.setattr(
        setup,
        "run_command",
        lambda command, **kwargs: commands.append((command, kwargs)),
    )

    setup.setup_python_env("~/project")

    venv = str(repo / "venv")
    assert commands == [
        (["python3", "-m", "venv", venv], {}),
        ([f"{venv}/bin/pip", "install", "--upgrade", "pip"], {"cwd": str(repo)}),
        ([f"{venv}/bin/pip", "install", "-r", "requirements.txt"], {"cwd": str(repo)}),
    ]


def test_setup_python_env_reuses_existing_venv(monkeypatch, tmp_path):
    repo = tmp_path / "project"
    monkeypatch.setattr(setup.os.path, "expanduser", lambda _path: str(repo))
    monkeypatch.setattr(setup.os.path, "isdir", lambda _path: True)
    commands = []
    monkeypatch.setattr(
        setup, "run_command", lambda command, **kwargs: commands.append(command)
    )

    setup.setup_python_env("~/project")

    assert len(commands) == 2
    assert all(command[0] == str(repo / "venv" / "bin" / "pip") for command in commands)


def test_configure_git_updates_only_values_that_differ(monkeypatch):
    queried = iter([b"Existing Name\n", b"old@example.test\n"])
    monkeypatch.setattr(
        setup.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout=next(queried)),
    )
    commands = []
    monkeypatch.setattr(setup, "run_command", lambda command: commands.append(command))

    setup.configure_git("Existing Name", "new@example.test")

    assert commands == [["git", "config", "--global", "user.email", "new@example.test"]]


def test_directory_path_and_environment_helpers(monkeypatch, tmp_path):
    home = tmp_path / "home"
    projects = home / "Projects"
    tools = home / "Tools"
    bashrc = home / ".bashrc"
    monkeypatch.setattr(setup.os.path, "expanduser", lambda path: str(home / path[2:]))
    made = []
    monkeypatch.setattr(setup.os, "makedirs", lambda path, **kwargs: made.append(path))
    setup.create_directories()
    assert made == [str(projects), str(tools)]

    monkeypatch.setenv("PATH", "/bin")
    monkeypatch.setattr(setup.os.path, "exists", lambda _path: False)
    opened = []

    class _File:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def write(self, value):
            opened.append(value)

    monkeypatch.setattr("builtins.open", lambda path, mode: _File())
    setup.update_env_variables()
    assert setup.os.environ["PATH"].endswith(str(tools))
    assert opened == ["\nexport PATH=$PATH:$HOME/Tools\n"]
    assert bashrc == home / ".bashrc"


def test_git_checkout_pull_and_commit_helpers(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    monkeypatch.setattr(setup.os.path, "expanduser", lambda _path: str(repo))
    commands = []
    monkeypatch.setattr(
        setup,
        "run_command",
        lambda command, **kwargs: commands.append((command, kwargs)),
    )

    setup.checkout_branch("feature")
    setup.pull_latest()
    setup.commit_and_push("Save work", remote="upstream", branch="feature")

    assert commands == [
        (["git", "fetch"], {"cwd": str(repo)}),
        (["git", "checkout", "feature"], {"cwd": str(repo)}),
        (["git", "pull", "--ff-only"], {"cwd": str(repo)}),
        (["git", "add", "."], {"cwd": str(repo)}),
        (["git", "commit", "-m", "Save work"], {"cwd": str(repo)}),
        (["git", "push", "upstream", "feature"], {"cwd": str(repo)}),
    ]
