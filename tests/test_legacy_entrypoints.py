"""Exercise retained script entry points without host changes or real commands."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "src/huey/memory/PY"


def _load_script(monkeypatch, filename: str, name: str | None = None):
    module_name = name or f"coverage_{Path(filename).stem.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, LEGACY / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("filename", "release"),
    [
        ("update_sources_to_forky.py", "forky"),
        ("update_sources_to_trixie.py", "trixie"),
    ],
)
def test_retained_apt_migration_scripts_update_only_requested_release(
    filename, release, monkeypatch, tmp_path, capsys
):
    module = _load_script(monkeypatch, filename)
    assert module.convert_line(
        "# deb http://example stable main\n", release
    ).startswith("#")
    assert module.convert_line("deb http://example stable main\n", release) == (
        f"deb http://example {release} main\n"
    )
    assert (
        module.convert_line(
            "deb-src [signed-by=/key] http://example stable-updates main\n", release
        )
        == f"deb-src [signed-by=/key] http://example {release}-updates main\n"
    )
    assert module.convert_line(
        f"deb http://example {release} main\n", release
    ).endswith(f"{release} main\n")
    assert module.convert_line("not a source line\n", release) == "not a source line\n"

    source = tmp_path / "sources.list"
    source.write_text("deb http://example stable main\n", encoding="utf-8")
    monkeypatch.setattr(module, "SOURCE_FILE", str(source))
    monkeypatch.setattr(module, "BACKUP_FILE", str(source) + ".bak")
    monkeypatch.setattr(module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(sys, "argv", [filename])
    module.main()
    assert source.read_text(encoding="utf-8") == f"deb http://example {release} main\n"
    assert Path(str(source) + ".bak").read_text(encoding="utf-8") == (
        "deb http://example stable main\n"
    )
    assert f"sources.list updated to {release}" in capsys.readouterr().out


def test_apt_migration_scripts_refuse_non_root_and_missing_file(monkeypatch, tmp_path):
    module = _load_script(monkeypatch, "update_sources_to_forky.py")
    monkeypatch.setattr(module.os, "geteuid", lambda: 1000)
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert exc.value.code == 1

    monkeypatch.setattr(module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(module, "SOURCE_FILE", str(tmp_path / "missing.list"))
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert exc.value.code == 1


def test_sync_pygpt_structure_copies_only_missing_or_placeholder_files(tmp_path):
    from huey.memory.PY import sync_pygpt_structure as syncer

    source = tmp_path / "source"
    target = tmp_path / "target"
    (source / "nested").mkdir(parents=True)
    (source / "keep.txt").write_text("source value", encoding="utf-8")
    (source / "nested" / "new.txt").write_text("new value", encoding="utf-8")
    (target / "nested").mkdir(parents=True)
    (target / "keep.txt").write_text("# real content", encoding="utf-8")
    (target / "placeholder.txt").write_text(
        "# Placeholder for generated content\n", encoding="utf-8"
    )
    (source / "placeholder.txt").write_text("replacement", encoding="utf-8")

    syncer.sync(str(source), str(target), depth=2)
    assert (target / "keep.txt").read_text() == "# real content"
    assert (target / "placeholder.txt").read_text() == "replacement"
    assert (target / "nested" / "new.txt").read_text() == "new value"

    syncer.sync(str(source), str(target), depth=0)
    assert (target / "nested" / "new.txt").read_text() == "new value"
    assert syncer._should_copy_file(str(target / "keep.txt")) is False
    missing = target / "missing.txt"
    assert syncer._should_copy_file(str(missing)) is True


def test_subos_commands_user_setup_and_environment_paths(monkeypatch, tmp_path):
    from huey.memory.PY import subos_manager

    commands = []
    monkeypatch.setattr(
        subos_manager, "run_command", lambda command: commands.append(command)
    )
    subos_manager.update_system()
    subos_manager.install_tools()
    assert commands[0:2] == [["apt-get", "update"], ["apt-get", "upgrade", "-y"]]
    assert commands[2][0:3] == ["apt-get", "install", "-y"]
    assert "docker.io" in commands[2]

    monkeypatch.setattr(subos_manager.pwd, "getpwnam", lambda _name: object())
    subos_manager.create_user("exists")
    assert len(commands) == 3
    monkeypatch.setattr(
        subos_manager.pwd,
        "getpwnam",
        lambda name: (_ for _ in ()).throw(KeyError(name)),
    )
    subos_manager.create_user("new-user")
    assert commands[-1] == ["useradd", "-m", "new-user"]

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(
        subos_manager.os.path,
        "expanduser",
        lambda value: str(home / value.removeprefix("~/")),
    )
    subos_manager.configure_environment()
    bashrc = home / ".bashrc"
    assert os.environ["SUBOS_PATH"] == str(home / "SubOS")
    assert bashrc.read_text().count("export SUBOS_PATH") == 1
    subos_manager.configure_environment()
    assert bashrc.read_text().count("export SUBOS_PATH") == 1

    changed = []
    monkeypatch.setattr(subos_manager.os, "chdir", changed.append)
    subos_manager.deploy_subos()
    assert changed == [str(home / "SubOS")]
    assert commands[-1] == ["docker-compose", "up", "-d"]


def test_gui_scaling_handles_modes_bad_values_and_tk_failures(monkeypatch):
    from huey.memory.PY import gui_scaling

    scale_calls = []
    configured = []

    class Font:
        def configure(self, **kwargs):
            configured.append(kwargs)

    monkeypatch.setattr(gui_scaling, "tk", object())
    monkeypatch.setattr(
        gui_scaling, "tkfont", SimpleNamespace(nametofont=lambda _name: Font())
    )
    root = SimpleNamespace(
        tk=SimpleNamespace(call=lambda *args: scale_calls.append(args))
    )
    gui_scaling.apply_scaling(root, "1080p")
    assert scale_calls[-1] == ("tk", "scaling", 1.0)
    assert configured[-1] == {"size": 10, "family": "Lato"}

    monkeypatch.setenv("SCREEN_FACTOR", "bad")
    monkeypatch.setenv("SCREEN_FONT_SIZE", "also-bad")
    gui_scaling.apply_scaling(root, "custom")
    assert scale_calls[-1] == ("tk", "scaling", 1.5)
    assert configured[-1] == {"size": 12, "family": "Lato"}

    gui_scaling.apply_scaling(root, None)
    assert scale_calls[-1] == ("tk", "scaling", 2.0)
    bad_root = SimpleNamespace(
        tk=SimpleNamespace(call=Mock(side_effect=RuntimeError("bad tk")))
    )
    bad_font = SimpleNamespace(nametofont=Mock(side_effect=ValueError("missing font")))
    monkeypatch.setattr(gui_scaling, "tkfont", bad_font)
    gui_scaling.apply_scaling(bad_root, "4k")
    monkeypatch.setattr(gui_scaling, "tk", None)
    gui_scaling.apply_scaling(root, "1080p")


def test_huey_deployment_script_checks_tools_and_runs_requested_steps(
    monkeypatch, tmp_path
):
    module = _load_script(monkeypatch, "Huey.py")
    with pytest.raises(RuntimeError, match="Build Huey Docker Image"):
        module.check_error(SimpleNamespace(returncode=2), "Build Huey Docker Image")
    module.check_error(SimpleNamespace(returncode=0), "ok")

    monkeypatch.setattr(module.shutil, "which", lambda name: f"/usr/bin/{name}")
    module.require_tools(["docker", "kubectl"])
    monkeypatch.setattr(module.shutil, "which", lambda _name: None)
    with pytest.raises(EnvironmentError, match="docker, kubectl"):
        module.require_tools(["docker", "kubectl"])

    workdir = tmp_path / "work"
    module.prepare_environment(str(workdir))
    assert workdir.is_dir()
    calls = []
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda command, **_kwargs: calls.append(command)
        or SimpleNamespace(returncode=0),
    )
    module.build_image("huey:test", str(tmp_path))
    monkeypatch.chdir(workdir)
    module.deploy_huey(str(workdir), "compose.yml", "cluster.yaml")
    assert calls == [
        ["docker", "build", "-t", "huey:test", str(tmp_path)],
        ["docker-compose", "-f", "compose.yml", "up", "-d"],
        ["kubectl", "apply", "-f", "cluster.yaml"],
    ]

    monkeypatch.setattr(module, "require_tools", lambda _tools: None)
    monkeypatch.setattr(module, "prepare_environment", lambda _workdir: None)
    decisions = []
    monkeypatch.setattr(
        module, "build_image", lambda *args: decisions.append(("build", args))
    )
    monkeypatch.setattr(
        module, "deploy_huey", lambda *args: decisions.append(("deploy", args))
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["Huey.py", "--build-only", "--workdir", str(workdir), "--tag", "v1"],
    )
    module.main()
    assert decisions == [("build", ("v1", "."))]
