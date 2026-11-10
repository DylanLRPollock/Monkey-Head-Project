"""Tests for the legacy fixture registry and CLI output utility."""

from __future__ import annotations

import hashlib
import json
import logging

import pytest

from huey.memory.PY import cli_print
from huey.memory.PY import fixture_registry


def test_fixture_record_json_conversion_and_registry_round_trip(tmp_path):
    path = tmp_path / "fixture.wav"
    path.write_bytes(b"fixture bytes")
    registry = fixture_registry.FixtureRegistry(tmp_path / "nested" / "registry.json")
    assert registry.load() == {}

    record = registry.register("audio-one", path, notes="sample")
    assert record.sha256 == hashlib.sha256(b"fixture bytes").hexdigest()
    assert record.size_bytes == len(b"fixture bytes")
    assert record.notes == "sample"
    data = record.to_json_dict()
    assert fixture_registry.FixtureRecord.from_json_dict(data) == record
    assert registry.get("audio-one") == record
    saved = json.loads(registry.registry_path.read_text())
    assert saved["schema"] == "huey.v1.fixture_registry"
    assert list(saved["fixtures"]) == ["audio-one"]


def test_fixture_registry_validation_overwrite_and_get_errors(tmp_path):
    registry = fixture_registry.FixtureRegistry(tmp_path / "registry.json")
    source = tmp_path / "sample.bin"
    source.write_bytes(b"first")

    with pytest.raises(ValueError, match="fixture_id is required"):
        registry.register("", source)
    with pytest.raises(FileNotFoundError, match="Fixture file not found"):
        registry.register("missing", tmp_path / "absent")

    original = registry.register("same", source)
    with pytest.raises(ValueError, match="Fixture already registered"):
        registry.register("same", source)
    source.write_bytes(b"second")
    replacement = registry.register("same", source, overwrite=True)
    assert replacement.sha256 != original.sha256
    with pytest.raises(KeyError):
        registry.get("absent")
    with pytest.raises(FileExistsError, match="overwrite is false"):
        registry.save({"same": replacement}, overwrite=False)


def test_fixture_registry_cli_add_and_list(capsys, tmp_path):
    source = tmp_path / "audio.raw"
    source.write_bytes(b"audio")
    registry = tmp_path / "registry.json"

    assert (
        fixture_registry.main(
            [
                str(registry),
                "add",
                "demo",
                str(source),
                "--kind",
                "audio",
                "--notes",
                "local",
            ]
        )
        == 0
    )
    added = json.loads(capsys.readouterr().out)
    assert added["fixture_id"] == "demo"
    assert added["notes"] == "local"

    assert fixture_registry.main([str(registry), "list"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["demo"]["kind"] == "audio"


def test_fixture_registry_cli_overwrite_flag(capsys, tmp_path):
    source = tmp_path / "audio.raw"
    source.write_bytes(b"a")
    registry = tmp_path / "registry.json"
    fixture_registry.main([str(registry), "add", "demo", str(source)])
    capsys.readouterr()
    source.write_bytes(b"b")

    assert (
        fixture_registry.main(
            [str(registry), "add", "demo", str(source), "--overwrite"]
        )
        == 0
    )
    record = json.loads(capsys.readouterr().out)
    assert record["sha256"] == hashlib.sha256(b"b").hexdigest()


def test_fixture_sha256_reads_multiple_chunks(tmp_path):
    source = tmp_path / "large.bin"
    content = b"x" * (1024 * 1024 + 13)
    source.write_bytes(content)
    assert fixture_registry.sha256_file(source) == hashlib.sha256(content).hexdigest()


def test_cli_config_defaults_and_json_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cli = cli_print.CLI("absent.json")
    assert cli.log_file == "CLI_LOG.json"
    assert "warning" in cli.valid_message_types

    config = tmp_path / "cli.json"
    config.write_text(
        json.dumps({"log_file": "custom.log", "valid_message_types": ["status"]})
    )
    configured = cli_print.CLI(str(config))
    assert configured.log_file == "custom.log"
    assert configured.valid_message_types == ["status"]


def test_cli_logging_redirects_file_handler_and_uses_requested_level(
    tmp_path, monkeypatch
):
    log_path = tmp_path / "output.log"
    handler = logging.FileHandler(log_path)
    logger = logging.getLogger("test-cli-print")
    logger.handlers = [handler]
    monkeypatch.setattr(cli_print, "configure_logging", lambda: logger)
    cli = cli_print.CLI.__new__(cli_print.CLI)
    cli.log_file = str(log_path)
    cli.setup_logging()
    assert handler.baseFilename == str(log_path)

    records = []
    monkeypatch.setattr(
        cli_print.logging, "log", lambda **kwargs: records.append(kwargs)
    )
    cli.log_message("message", "warning")
    assert records == [{"level": logging.WARNING, "msg": "message"}]
    handler.close()


def test_cli_prints_default_alert_and_user_input_messages(monkeypatch, capsys):
    cli = cli_print.CLI("missing.json")
    logged = []
    monkeypatch.setattr(
        cli, "log_message", lambda message, kind: logged.append((message, kind))
    )

    assert cli.print_message("ready", "status") is None
    assert capsys.readouterr().out.strip() == "> Status: ready"
    assert cli.print_message("careful", "alert") is None
    assert (
        capsys.readouterr().out.strip()
        == "Alert has been triggered & program may fail!"
    )

    monkeypatch.setattr("builtins.input", lambda prompt: f"answer to {prompt}")
    response = cli.print_message("name?", "user_input")
    assert response.endswith("User_input: name?")
    assert logged[-1][1] == "user_input"


def test_cli_validation_and_graceful_exit(monkeypatch, capsys):
    cli = cli_print.CLI("missing.json")
    monkeypatch.setattr(cli, "log_message", lambda *_args: None)
    with pytest.raises(SystemExit):
        cli.print_message("", "status")
    output = capsys.readouterr().out
    assert "Error: output_message cannot be an empty string" in output
    assert "Cleaning up resources" in output
    assert "Exiting the program" in output

    with pytest.raises(SystemExit):
        cli.graceful_exit()


def test_cli_validates_types_and_handles_exceptions(monkeypatch, capsys):
    cli = cli_print.CLI("missing.json")
    monkeypatch.setattr(cli, "log_message", lambda *_args: None)
    with pytest.raises(SystemExit):
        cli.print_message("value", "unknown")
    assert "Invalid message_type provided" in capsys.readouterr().out

    with pytest.raises(SystemExit):
        cli.handle_exception(RuntimeError, "operation")
    output = capsys.readouterr().out
    assert "encountered a RuntimeError" in output
    assert "Alert has been triggered" in output


def test_cli_process_messages_dispatches_each_message(monkeypatch):
    cli = cli_print.CLI("missing.json")
    calls = []
    monkeypatch.setattr(cli, "print_message", lambda *args: calls.append(args))

    cli.process_messages([("one", "info"), ("two", "warning")])

    assert sorted(calls) == [("one", "info"), ("two", "warning")]


def test_cli_validation_rejects_non_string_and_blank_types(monkeypatch):
    cli = cli_print.CLI("missing.json")
    monkeypatch.setattr(cli, "log_message", lambda *_args: None)
    for message, kind in ((7, "status"), ("value", 7), ("value", " ")):
        with pytest.raises(SystemExit):
            cli.print_message(message, kind)


def test_fixture_registry_cli_returns_after_unknown_command(monkeypatch, tmp_path):
    class ParserStub:
        def __init__(self, **_kwargs):
            pass

        def add_argument(self, *_args, **_kwargs):
            return None

        def add_subparsers(self, **_kwargs):
            return self

        def add_parser(self, *_args, **_kwargs):
            return self

        def parse_args(self, _argv):
            return type(
                "Args", (), {"registry": tmp_path / "registry.json", "command": "other"}
            )()

    monkeypatch.setattr(fixture_registry.argparse, "ArgumentParser", ParserStub)
    assert fixture_registry.main([]) == 0
