import sys
from run import main


def test_run_module_option(monkeypatch, capsys):
    test_args = ["prog", "--module", "tests.dummy_module"]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    captured = capsys.readouterr().out.strip()
    assert captured == "dummy module executed"
