import sys
from unittest.mock import patch

import pytest

pytest.importorskip("PIL.Image")

from huey.config import load_config
from huey.cli import parse_arguments, run_cli
from huey.exceptions import HueyError, DataNotFoundError, InvalidInputError


# Tests for configuration loading


def test_load_config_success(tmp_path):
    cfg = tmp_path / "cfg.yml"
    cfg.write_text("foo: bar")
    result = load_config(str(cfg))
    assert result["foo"] == "bar"


def test_load_config_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "missing.yml"))


# Tests for CLI argument parsing and invocation


def test_parse_arguments_verbose():
    test_args = ["prog", "--config", "file.yml", "--verbose"]
    with patch.object(sys, "argv", test_args):
        args = parse_arguments()
        assert args.config == "file.yml"
        assert args.verbose is True


def test_run_cli_invokes_main(tmp_path):
    cfg = tmp_path / "cfg.yml"
    cfg.write_text("logging:\n  level: INFO")
    test_args = ["prog", "--config", str(cfg)]
    with patch.object(sys, "argv", test_args), patch("huey.cli.huey_main") as main_mock:
        run_cli()
        main_mock.assert_called_once_with(config_file=str(cfg))


# Tests for exception hierarchy


def test_exceptions_inherit_from_base():
    assert issubclass(DataNotFoundError, HueyError)
    assert issubclass(InvalidInputError, HueyError)
