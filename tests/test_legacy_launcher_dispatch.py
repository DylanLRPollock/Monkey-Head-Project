"""Test the deprecated unified launcher without importing host scripts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture
def launcher(monkeypatch):
    calls = []
    for name in ("fresh_install", "installer", "repair", "uninstaller", "run"):
        module = ModuleType(name)
        if name == "repair":
            module.REPO_URL = "https://example.invalid/huey.git"
        if name == "fresh_install":
            module.run_fresh_install = lambda *args, **kwargs: (
                calls.append(("fresh", args, kwargs)) or 5
            )
        if name == "installer":
            module.run_installer = lambda **kwargs: (
                calls.append(("install", kwargs)) or 6
            )
        if name == "uninstaller":
            module.run_uninstaller = lambda **kwargs: (
                calls.append(("uninstall", kwargs)) or 7
            )
        if name == "run":
            module.main = lambda: calls.append(("run", list(sys.argv)))
        monkeypatch.setitem(sys.modules, name, module)

    source = (
        Path(__file__).parents[1] / "src" / "huey" / "memory" / "PY" / "launcher.py"
    )
    spec = importlib.util.spec_from_file_location("legacy_launcher_under_test", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module, calls


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (None, ["run", ["pytest"]]),
        (
            ["run", "--cli", "--workdir", "/tmp/app"],
            ["run", ["pytest", "--cli", "--workdir", "/tmp/app"]],
        ),
    ],
)
def test_launcher_defaults_to_runtime_and_forwards_unparsed_args(
    launcher, monkeypatch, argv, expected
):
    module, calls = launcher
    monkeypatch.setattr(
        sys, "argv", ["pytest"] if argv is None else ["pytest", "ignored"]
    )
    module.main(argv)
    assert calls[0][0] == expected[0]
    if argv is None:
        assert calls[0][1] == expected[1]
    else:
        assert calls[0][1][1:] == expected[1][1:]


def test_launcher_install_and_uninstall_apply_role_and_confirmation(launcher):
    module, calls = launcher
    with pytest.raises(SystemExit) as install:
        module.main(["install", "--yes", "--dry-run"])
    assert install.value.code == 6
    assert calls[-1] == (
        "install",
        {"confirmed": True, "actor_role": "operator", "dry_run": True},
    )

    with pytest.raises(SystemExit) as uninstall:
        module.main(["uninstall"])
    assert uninstall.value.code == 7
    assert calls[-1] == ("uninstall", {"confirmed": False, "actor_role": None})


def test_launcher_fresh_install_defaults_and_overrides_repository(launcher):
    module, calls = launcher
    with pytest.raises(SystemExit) as default:
        module.main(["fresh-install"])
    assert default.value.code == 5
    assert calls[-1] == (
        "fresh",
        ("local", "https://example.invalid/huey.git"),
        {"confirmed": False, "actor_role": None},
    )

    with pytest.raises(SystemExit):
        module.main(
            [
                "fresh-install",
                "--source",
                "github",
                "--repo",
                "https://git.example/repo",
                "--yes",
            ]
        )
    assert calls[-1] == (
        "fresh",
        ("github", "https://git.example/repo"),
        {"confirmed": True, "actor_role": "admin"},
    )


def test_launcher_system_check_returns_without_exiting(launcher, monkeypatch):
    module, calls = launcher
    checks = []
    monkeypatch.setattr(module, "system_check", lambda: checks.append("checked"))
    assert module.main(["system-check", "unused"]) is None
    assert checks == ["checked"]
    assert calls == []
