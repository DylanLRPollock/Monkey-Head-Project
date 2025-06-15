import sys
from monkey_head import main as main_mod


def test_parse_args_defaults():
    args = main_mod.parse_args([])
    assert args.skip_setup is False
    assert args.host == "0.0.0.0"
    assert args.port == 4488


def test_main_respects_skip(monkeypatch):
    called = {}
    monkeypatch.setattr(main_mod, "run_setup", lambda: called.setdefault("setup", True))
    monkeypatch.setattr(main_mod.app, "run", lambda host, port: called.setdefault("run", (host, port)))
    monkeypatch.setattr(sys, "argv", ["main.py", "--skip-setup", "--port", "1234"])
    main_mod.main()
    assert "setup" not in called
    assert called["run"] == ("0.0.0.0", 1234)


def test_main_runs_setup(monkeypatch):
    called = {}
    monkeypatch.setattr(main_mod, "run_setup", lambda: called.setdefault("setup", True))
    monkeypatch.setattr(main_mod.app, "run", lambda host, port: called.setdefault("run", (host, port)))
    monkeypatch.setattr(sys, "argv", ["main.py"])
    main_mod.main()
    assert called["setup"] is True
    assert called["run"] == ("0.0.0.0", 4488)
