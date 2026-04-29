# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Run Sys Code module (tests)

import sys

from run import main


def test_run_sys_code(monkeypatch):
    called = {}

    class FakeProcess:
        def __init__(self):
            self.returncode = 0
            self.stdout = b"output"
            self.stderr = b""

    def fake_run(cmd, stdout=None, stderr=None):
        called["cmd"] = cmd
        return FakeProcess()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("run.launch_gui", lambda: None)
    monkeypatch.setattr("run._load_cli", lambda: lambda: None)
    monkeypatch.setattr("hueyos.core.system_checks.check_os_support", lambda: None)
    monkeypatch.setattr(
        "hueyos.core.system_checks.check_python_version", lambda: None
    )
    monkeypatch.setattr(sys, "argv", ["run.py", "--sys-code", "echo hi"])
    main()
    assert called.get("cmd") == ["echo", "hi"]
