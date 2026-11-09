# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Run System Check module (tests)

from huey.memory.PY.run import main


def test_system_check_called(monkeypatch):
    called = {}

    def fake_check(*_args, **_kwargs):
        called["done"] = True

    monkeypatch.setattr("huey.os.core.system_checks.system_check", fake_check)
    monkeypatch.setattr("huey.os.core.system_checks.check_os_support", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("huey.os.core.system_checks.check_python_version", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("huey.memory.PY.run.launch_gui", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("huey.memory.PY.run._load_cli", lambda: lambda *_args, **_kwargs: None)
    monkeypatch.setattr("sys.argv", ["run.py", "--system-check"])
    main()
    assert called.get("done") is True
