"""Exercise legacy utility file and credential handling without host changes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

from huey.memory.PY import add_project_headers as headers
from huey.memory.PY import set_api_keys
from huey.memory.PY import update_prompts


def test_header_humanization_and_building_cover_package_and_script_types(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(headers, "REPO_ROOT", tmp_path)
    assert headers.humanize_path(tmp_path / "__init__.py") == "Root package initializer"
    assert (
        headers.humanize_path(tmp_path / "src" / "__init__.py")
        == "Package initializer for src"
    )
    assert headers.humanize_path(tmp_path / "__main__.py") == "Package entry point"
    assert (
        headers.humanize_path(tmp_path / "src" / "__main__.py")
        == "Module entry point for src"
    )
    assert headers.humanize_path(tmp_path / "my_file-name.py") == "My File Name module"
    assert headers.humanize_path(tmp_path / "setup.sh") == "Setup shell script"
    assert headers.humanize_path(tmp_path / "setup.bat") == "Setup batch script"
    assert headers.build_header(tmp_path / "setup.bat")[0].startswith("REM ")
    assert headers.build_header(tmp_path / "setup.py")[0].startswith("# ")


def test_header_file_read_write_detection_and_insertion_positions(tmp_path):
    path = tmp_path / "sample.py"
    headers.write_lines(
        path, ["#!/usr/bin/env python", "# coding: utf-8", "print('x')"]
    )
    lines = headers.read_lines(path)
    assert headers.insertion_index(path, lines) == 2
    assert headers.has_header(["", "REM Monkey Head Project"])
    assert not headers.has_header(["first"] * 10 + ["# Monkey Head Project"])
    assert (
        headers.insertion_index(tmp_path / "sample.sh", ["#!/bin/sh", "echo ok"]) == 1
    )
    assert headers.insertion_index(path, ["print('x')"]) == 0


def test_ensure_header_is_idempotent_and_dry_run_does_not_write(tmp_path, monkeypatch):
    monkeypatch.setattr(headers, "REPO_ROOT", tmp_path)
    path = tmp_path / "new.py"
    path.write_text("#!/usr/bin/env python\n# coding: utf-8\nprint('ok')\n")

    assert headers.ensure_header(path, dry_run=True) is True
    assert path.read_text().startswith("#!/usr/bin/env python\n# coding: utf-8\n")
    assert headers.ensure_header(path) is True
    assert headers.has_header(headers.read_lines(path))
    assert headers.ensure_header(path) is False


def test_find_targets_and_main_check_and_write_paths(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(headers, "REPO_ROOT", tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "no_header.PY").write_text("print('missing')\n")
    (tmp_path / "src" / "script.sh").write_text("echo hi\n")
    (tmp_path / "src" / "ignored.txt").write_text("skip\n")

    assert {path.name for path in headers.find_targets(tmp_path)} == {
        "no_header.PY",
        "script.sh",
    }
    monkeypatch.setattr(
        headers, "parse_args", lambda: argparse.Namespace(check=True, paths=[tmp_path])
    )
    assert headers.main() == 1
    assert "no_header.PY" in capsys.readouterr().out

    monkeypatch.setattr(
        headers, "parse_args", lambda: argparse.Namespace(check=False, paths=[tmp_path])
    )
    assert headers.main() == 0
    monkeypatch.setattr(
        headers, "parse_args", lambda: argparse.Namespace(check=True, paths=[tmp_path])
    )
    assert headers.main() == 0
    assert capsys.readouterr().out == ""
    monkeypatch.setattr(
        headers, "parse_args", lambda: argparse.Namespace(check=False, paths=[tmp_path])
    )
    assert headers.main() == 1


def test_header_main_handles_single_file_argument(tmp_path, monkeypatch):
    monkeypatch.setattr(headers, "REPO_ROOT", tmp_path)
    file_path = tmp_path / "single.py"
    file_path.write_text("print('one')\n")
    monkeypatch.setattr(
        headers,
        "parse_args",
        lambda: argparse.Namespace(check=False, paths=[file_path]),
    )
    assert headers.main() == 0
    assert headers.has_header(headers.read_lines(file_path))


def test_rewrite_prompt_rules_and_dry_run_leave_source_unchanged(tmp_path):
    source = tmp_path / "prompts.csv"
    source.write_text(
        "# comment\nAct,Prompt,For Developers\n"
        'artist,"I want you to act as an artist. I want you to paint boldly",yes\n'
        'engineer,"I want you to build carefully",no\n'
        "short,row\n\n",
        encoding="utf-8",
    )

    rows = update_prompts.rewrite_prompts(source, dry_run=True)

    assert rows == [
        ("artist", "You are an artist. You should paint boldly", "yes"),
        ("engineer", "You are an engineer. You should build carefully", "no"),
    ]
    assert source.read_text(encoding="utf-8").startswith("# comment\n")
    assert not source.with_suffix(".csv.bak").exists()


def test_rewrite_prompts_writes_backup_and_supports_separate_output(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("# source\nAct,Prompt,For Developers\nhelper,Help me,yes\n")
    rows = update_prompts.rewrite_prompts(source)
    assert rows[0][1] == "You are a helper. Help me"
    assert (
        source.with_suffix(".csv.bak").read_text()
        == "# source\nAct,Prompt,For Developers\nhelper,Help me,yes\n"
    )
    assert source.read_text().startswith("# source\nAct,Prompt,For Developers\n")

    output = tmp_path / "rewritten.csv"
    update_prompts.rewrite_prompts(source, output_file=output, backup=False)
    assert output.exists()
    assert not output.with_suffix(".csv.bak").exists()


def test_rewrite_prompts_rejects_missing_comment_or_header(tmp_path):
    source = tmp_path / "invalid.csv"
    source.write_text("Act,Prompt,For Developers\n")
    with pytest.raises(ValueError, match="comment line and a header row"):
        update_prompts.rewrite_prompts(source)


def test_update_prompt_cli_accepts_options_and_reports_count(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "prompts.csv"
    source.write_text("# comment\nAct,Prompt,For Developers\nhelper,Help me,yes\n")
    assert (
        update_prompts.main(["--input", str(source), "--dry-run", "--no-backup"]) == 0
    )
    assert "Processed 1 prompt rows" in capsys.readouterr().out
    monkeypatch.setattr(update_prompts, "DEFAULT_PROMPTS_FILE", source)
    assert update_prompts.main(["--dry-run"]) == 0


def test_api_key_load_save_filters_empty_values_and_sets_restrictive_mode(
    tmp_path, monkeypatch, capsys
):
    config = tmp_path / "config" / "pygpt_net" / "config.json"
    monkeypatch.setattr(set_api_keys, "CONFIG_PATH", str(config))
    assert set_api_keys.load_config() == {}
    assert set_api_keys.save_config({"openai": "  ", "bad": 3}) is False
    assert "No non-empty local keys" in capsys.readouterr().out

    assert set_api_keys.save_config({"openai": "secret", "blank": " "}) is True
    assert set_api_keys.load_config() == {"openai": "secret"}
    assert config.stat().st_mode & 0o777 == 0o600
    assert "local-only fallback" in capsys.readouterr().out


def test_api_key_save_warns_if_chmod_fails(tmp_path, monkeypatch, capsys):
    config = tmp_path / "config.json"
    monkeypatch.setattr(set_api_keys, "CONFIG_PATH", str(config))
    monkeypatch.setattr(
        set_api_keys.os,
        "chmod",
        lambda *_args: (_ for _ in ()).throw(OSError("denied")),
    )
    assert set_api_keys.save_config({"google": "key"}) is True
    assert "Could not set restrictive permissions" in capsys.readouterr().out


def test_prompt_service_choice_auto_and_manual(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _prompt: "1")
    assert set_api_keys.prompt_service_choice() == ["openai", "google", "deepseek"]
    answers = iter(["2", "y", "n", "Y"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert set_api_keys.prompt_service_choice() == ["openai", "deepseek"]


def test_prompt_keys_respects_environment_existing_values_and_blank_answers(
    monkeypatch, capsys
):
    monkeypatch.setenv("OPENAI_API_KEY", "environment-secret")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    answers = iter([" ", "deepseek-secret"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    values = {"api_key_google": "existing-google"}

    set_api_keys.prompt_keys(["openai", "google", "deepseek"], values)

    assert values == {
        "api_key_google": "existing-google",
        "api_key_deepseek": "deepseek-secret",
    }
    output = capsys.readouterr().out
    assert "leaving unchanged" in output
    assert "already present" in output


def test_api_key_main_handles_no_services_and_environment_only(monkeypatch, capsys):
    monkeypatch.setattr(set_api_keys, "load_config", lambda: {})
    monkeypatch.setattr(set_api_keys, "prompt_service_choice", lambda: [])
    set_api_keys.main()
    assert "No services selected" in capsys.readouterr().out

    monkeypatch.setattr(set_api_keys, "prompt_service_choice", lambda: ["openai"])
    monkeypatch.setattr(set_api_keys, "prompt_keys", lambda _services, _data: None)
    monkeypatch.setattr(set_api_keys, "save_config", lambda _data: False)
    set_api_keys.main()
    assert "Preferred setup" in capsys.readouterr().out


def test_api_key_main_reports_saved_local_config(monkeypatch, capsys):
    monkeypatch.setattr(set_api_keys, "load_config", lambda: {"openai": "secret"})
    monkeypatch.setattr(set_api_keys, "prompt_service_choice", lambda: ["openai"])
    monkeypatch.setattr(set_api_keys, "prompt_keys", lambda _services, _data: None)
    monkeypatch.setattr(set_api_keys, "save_config", lambda _data: True)
    set_api_keys.main()
    assert "Local fallback keys saved" in capsys.readouterr().out


def test_update_prompts_does_not_create_backup_when_target_is_distinct(tmp_path):
    source = tmp_path / "source.csv"
    target = tmp_path / "copy.csv"
    source.write_text("# comment\nAct,Prompt,For Developers\naide,Help me,no\n")
    update_prompts.rewrite_prompts(source, target)
    assert target.exists()
    assert not source.with_suffix(".csv.bak").exists()


def test_header_parse_args_uses_path_arguments(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["add_project_headers.py", "--check", "src"])
    args = headers.parse_args()
    assert args.check is True
    assert args.paths == [Path("src")]
