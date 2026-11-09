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

    def fake_run(cmd, **kwargs):
        called["cmd"] = cmd
        called["kwargs"] = kwargs
        return FakeProcess()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("run.launch_gui", lambda: None)
    monkeypatch.setattr("run._load_cli", lambda: lambda: None)
    monkeypatch.setattr("huey.os.core.system_checks.check_os_support", lambda: None)
    monkeypatch.setattr("huey.os.core.system_checks.check_python_version", lambda: None)
    monkeypatch.setattr(
        sys, "argv", ["run.py", "--sys-code", "echo hi", "--yes"]
    )
    main()
    assert called.get("cmd") == ["echo", "hi"]
    assert called["kwargs"]["shell"] is False
    assert called["kwargs"]["timeout"] == 300


def test_run_sys_code_denies_direct_calls_before_subprocess(monkeypatch):
    from huey.memory.PY.run import run_sys_code

    called = []
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: called.append(args))
    try:
        run_sys_code("echo hi")
    except PermissionError:
        pass
    else:
        raise AssertionError("unconfirmed system command was allowed")
    assert called == []


def test_run_sys_code_dry_run_skips_subprocess(monkeypatch):
    from huey.memory.PY.run import run_sys_code

    called = []
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: called.append(args))
    assert run_sys_code(
        "echo hi", confirmed=True, actor_role="admin", dry_run=True
    ) is False
    assert called == []
