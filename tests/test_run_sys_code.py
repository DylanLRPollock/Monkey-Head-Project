# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Run Sys Code module (tests)

from run import main
import sys


def test_run_sys_code(monkeypatch):
    called = {}

    class FakeProcess:
        def __init__(self):
            self.returncode = 0
            self.stdout = b"output"
            self.stderr = b""

    def fake_run(cmd, shell=True, stdout=None, stderr=None):
        called['cmd'] = cmd
        return FakeProcess()

    monkeypatch.setattr('subprocess.run', fake_run)
    monkeypatch.setattr('run.launch_gui', lambda: None)
    monkeypatch.setattr('run._load_cli', lambda: lambda: None)
    monkeypatch.setattr('monkey_head.core.system_checks.check_os_support', lambda: None)
    monkeypatch.setattr('monkey_head.core.system_checks.check_python_version', lambda: None)
    monkeypatch.setattr(sys, 'argv', ['run.py', '--sys-code', 'echo hi'])
    main()
    assert called.get('cmd') == 'echo hi'
