# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Run Manager Ui module (tests)

from huey.memory.PY.run import main


def test_manager_ui(monkeypatch):
    called = {}

    def fake_manager():
        called["manager"] = True

    monkeypatch.setattr("run.launch_manager_ui", fake_manager)
    monkeypatch.setattr("huey.memory.PY.run.launch_gui", lambda: None)
    monkeypatch.setattr("huey.memory.PY.run._load_cli", lambda: lambda: None)
    monkeypatch.setattr("huey.os.core.system_checks.check_os_support", lambda: None)
    monkeypatch.setattr("huey.os.core.system_checks.check_python_version", lambda: None)
    monkeypatch.setattr("sys.argv", ["run.py", "--manager-ui"])
    main()
    assert called.get("manager") is True
