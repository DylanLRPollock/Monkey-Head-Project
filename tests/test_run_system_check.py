# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Run System Check module (tests)

from run import main


def test_system_check_called(monkeypatch):
    called = {}

    def fake_check():
        called["done"] = True

    monkeypatch.setattr("hueyos.core.system_checks.system_check", fake_check)
    monkeypatch.setattr("hueyos.core.system_checks.check_os_support", lambda: None)
    monkeypatch.setattr("hueyos.core.system_checks.check_python_version", lambda: None)
    monkeypatch.setattr("run.launch_gui", lambda: None)
    monkeypatch.setattr("run._load_cli", lambda: lambda: None)
    monkeypatch.setattr("sys.argv", ["run.py", "--system-check"])
    main()
    assert called.get("done") is True
