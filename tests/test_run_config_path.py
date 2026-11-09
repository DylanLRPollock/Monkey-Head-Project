# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Run Config Path module (tests)

import os

from huey.memory.PY.run import main


def test_run_sets_config_env(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.ini"
    cfg.write_text(
        f"[logging]\nlog_level = INFO\nlog_file = {tmp_path}/app.log\nlog_max_bytes = 1024\n"
        "log_backup_count = 1\n"
    )
    monkeypatch.setattr("huey.memory.PY.run.launch_gui", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("huey.memory.PY.run._load_cli", lambda *_args, **_kwargs: lambda: None)
    monkeypatch.setattr("huey.os.core.system_checks.check_os_support", lambda: None)
    monkeypatch.setattr(
        "huey.os.core.system_checks.check_python_version",
        lambda: None,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["run.py", "--config", str(cfg)],
    )
    main()
    assert os.environ.get("MONKEY_HEAD_CONFIG") == str(cfg)
