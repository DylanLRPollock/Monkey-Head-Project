"""Directly cover legacy CLI dispatch and failure branches."""

from __future__ import annotations

import argparse
import subprocess
from types import SimpleNamespace

import pytest

from huey.memory.PY import cli


def _run_args(**overrides):
    values = {
        "ml": False,
        "cloud": False,
        "profile": [],
        "skip_checks": True,
        "manager_ui": False,
        "minimal": False,
        "cli": False,
        "gui": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_init_verbose_and_system_check(monkeypatch, capsys, tmp_path):
    from huey.os.utils import auto_sort, paths

    calls = []
    monkeypatch.setattr(paths, "get_memory_path", lambda **_kw: tmp_path)
    monkeypatch.setattr(
        paths,
        "ensure_subdirectory",
        lambda name: calls.append(name) or tmp_path / name,
    )
    monkeypatch.setattr(
        auto_sort, "get_extension_map", lambda: {"a": "JSON", "b": "PDF"}
    )
    from huey.os import system_checks

    monkeypatch.setattr(system_checks, "system_check", lambda: {"b": False, "a": True})

    assert cli._cmd_init(argparse.Namespace(verbose=True, run_checks=True)) == 0

    output = capsys.readouterr().out
    assert calls == ["RAW", "LOGS", "JSON", "PDF"]
    assert "Memory initialised" in output
    assert "  - " in output
    assert "a: OK" in output
    assert "b: WARN" in output


def test_profile_normalization_discards_blanks_and_duplicates():
    assert cli._normalise_profiles([" ml ", "", "cloud", "ml", " cloud "]) == [
        "ml",
        "cloud",
    ]


def test_resolve_shadow_root_explicit_log_dir_fallback_and_errors(
    monkeypatch, tmp_path
):
    from huey.os.utils import paths

    explicit = tmp_path / "explicit"
    explicit.mkdir()
    logs = tmp_path / "logs"
    (logs / "hims-shadow").mkdir(parents=True)
    memory = tmp_path / "memory"
    fallback = memory / "V1" / "runs" / "hims-shadow"
    fallback.mkdir(parents=True)
    monkeypatch.setattr(paths, "get_memory_path", lambda **_kw: memory)

    assert (
        cli._resolve_shadow_hims_root(argparse.Namespace(shadow_root=str(explicit)))
        == explicit
    )
    assert (
        cli._resolve_shadow_hims_root(argparse.Namespace(log_dir=str(logs)))
        == logs / "hims-shadow"
    )
    assert cli._resolve_shadow_hims_root(argparse.Namespace()) == fallback
    with pytest.raises(RuntimeError, match="Shadow HIMS root not found"):
        cli._resolve_shadow_hims_root(
            argparse.Namespace(shadow_root=str(tmp_path / "missing"))
        )


def test_run_combines_profiles_and_dispatches_manager_ui(monkeypatch):
    called = []
    runtime = SimpleNamespace(launch_manager_ui=lambda: called.append("manager"))
    monkeypatch.setattr(cli, "import_module", lambda _name: runtime)
    monkeypatch.setenv("HUEY_PROFILES", "cloud,existing")

    assert (
        cli._cmd_run(_run_args(ml=True, profile=["custom, ml"], manager_ui=True)) == 0
    )
    assert called == ["manager"]
    assert __import__("os").environ["HUEY_PROFILES"] == "ml,custom,cloud,existing"


@pytest.mark.parametrize(
    ("args", "runtime", "message"),
    [
        (
            _run_args(minimal=True),
            SimpleNamespace(),
            "Minimal CLI mode is not available",
        ),
        (_run_args(cli=True), SimpleNamespace(), "CLI launcher is not available"),
        (_run_args(), SimpleNamespace(), "GUI launcher is not available"),
    ],
)
def test_run_reports_unavailable_modes(monkeypatch, args, runtime, message):
    monkeypatch.setattr(cli, "import_module", lambda _name: runtime)
    with pytest.raises(RuntimeError, match=message):
        cli._cmd_run(args)


def test_run_missing_runtime_and_keyboard_interrupt(monkeypatch):
    def missing(_name):
        raise ModuleNotFoundError

    monkeypatch.setattr(cli, "import_module", missing)
    with pytest.raises(RuntimeError, match="Unable to locate runtime module"):
        cli._cmd_run(_run_args())

    runtime = SimpleNamespace(
        launch_gui=lambda: (_ for _ in ()).throw(KeyboardInterrupt())
    )
    monkeypatch.setattr(cli, "import_module", lambda _name: runtime)
    assert cli._cmd_run(_run_args()) == 130


def test_run_checks_and_cli_launcher(monkeypatch):
    from huey.os.core import system_checks

    checks = []
    monkeypatch.setattr(system_checks, "check_os_support", lambda: checks.append("os"))
    monkeypatch.setattr(
        system_checks, "check_python_version", lambda: checks.append("python")
    )
    ran = []
    runtime = SimpleNamespace(_load_cli=lambda: lambda: ran.append(True))
    monkeypatch.setattr(cli, "import_module", lambda _name: runtime)

    assert cli._cmd_run(_run_args(cli=True, skip_checks=False)) == 0
    assert checks == ["os", "python"]
    assert ran == [True]


def test_run_command_dry_verbose_missing_and_nonzero(monkeypatch, capsys):
    assert cli._run_command(["tool", "--version"], dry_run=True, verbose=False) is None
    assert "[dry-run] tool --version" in capsys.readouterr().out

    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *_a, **_kw: subprocess.CompletedProcess(
            ["tool"], 0, stdout="out\n", stderr="warn\n"
        ),
    )
    assert cli._run_command(["tool"], dry_run=False, verbose=True).returncode == 0
    captured = capsys.readouterr()
    assert captured.out == "out\n"
    assert captured.err == "warn\n"

    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *_a, **_kw: (_ for _ in ()).throw(FileNotFoundError()),
    )
    with pytest.raises(RuntimeError, match="Command not found: absent"):
        cli._run_command(["absent"], dry_run=False, verbose=False)
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *_a, **_kw: subprocess.CompletedProcess(
            ["tool"], 7, stdout="", stderr=""
        ),
    )
    with pytest.raises(RuntimeError, match="exited with 7"):
        cli._run_command(["tool"], dry_run=False, verbose=False)


def test_deploy_errors_empty_selection_and_success(monkeypatch, tmp_path, capsys):
    args = argparse.Namespace(
        mode="docker",
        compose_file=str(tmp_path / "missing.yml"),
        manifest=str(tmp_path / "missing.yaml"),
        dry_run=True,
        verbose=False,
    )
    with pytest.raises(RuntimeError, match="Docker compose file not found"):
        cli._cmd_deploy(args)

    args.mode = "none"
    assert cli._cmd_deploy(args) == 0
    assert "No deployment tasks selected" in capsys.readouterr().out

    compose = tmp_path / "compose.yml"
    compose.write_text("services: {}", encoding="utf-8")
    args.mode = "docker"
    args.compose_file = str(compose)
    monkeypatch.setattr(cli.shutil, "which", lambda _name: None)
    with pytest.raises(RuntimeError, match="Docker executable not found"):
        cli._cmd_deploy(args)

    monkeypatch.setattr(cli.shutil, "which", lambda _name: "/usr/bin/docker")
    calls = []
    monkeypatch.setattr(
        cli, "_run_command", lambda command, **kw: calls.append((command, kw))
    )
    assert cli._cmd_deploy(args) == 0
    assert calls and calls[0][1]["dry_run"] is True


def test_memory_sort_text_and_missing_source(monkeypatch, capsys):
    from huey.os.utils import auto_sort

    summary = {
        "source": "/src",
        "destination": "/dst",
        "moved": ["a"],
        "skipped": ["b"],
    }
    monkeypatch.setattr(auto_sort, "auto_sort_memory", lambda **_kw: summary)
    args = argparse.Namespace(
        source="/src", destination="/dst", dry_run=False, json=False
    )
    assert cli._cmd_memory_sort(args) == 0
    output = capsys.readouterr().out
    assert "Moved 1 file(s)" in output
    assert "Skipped 1 file(s)" in output

    monkeypatch.setattr(
        auto_sort,
        "auto_sort_memory",
        lambda **_kw: (_ for _ in ()).throw(FileNotFoundError("gone")),
    )
    with pytest.raises(RuntimeError, match="gone"):
        cli._cmd_memory_sort(args)


def test_main_converts_handler_runtime_errors_to_exit_code(capsys):
    assert cli.main(["v1-run", "/does/not/exist", "--mock"]) == 1
    assert "Audio fixture not found" in capsys.readouterr().err
