# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Run Module Option module (tests)

import sys

from run import main


def test_run_module_option(monkeypatch, capsys):
    test_args = ["prog", "--module", "tests.dummy_module"]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    captured = capsys.readouterr().out.strip()
    assert captured == "dummy module executed"
