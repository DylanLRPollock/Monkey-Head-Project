# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Cli Print module (tests)

from monkey_head.cli_print import print_message
import pytest


def test_print_message_outputs(capsys):
    print_message("hello")
    print_message("warn", "warning")
    print_message("err", "error")
    captured = capsys.readouterr().out.strip().splitlines()
    assert captured == ["[INFO] hello", "[WARNING] warn", "[ERROR] err"]


def test_print_message_invalid():
    with pytest.raises(ValueError):
        print_message("hi", "invalid")
