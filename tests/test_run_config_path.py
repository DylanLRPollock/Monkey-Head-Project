from run import main
import os


def test_run_sets_config_env(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.ini"
    cfg.write_text(
        (
            "[logging]\nlog_level = INFO\nlog_file = {}/app.log\nlog_max_bytes = 1024\n"
            "log_backup_count = 1\n"
        ).format(tmp_path)
    )
    monkeypatch.setattr('run.launch_gui', lambda: None)
    monkeypatch.setattr('run._load_cli', lambda: lambda: None)
    monkeypatch.setattr('monkey_head.core.system_checks.check_os_support', lambda: None)
    monkeypatch.setattr(
        'monkey_head.core.system_checks.check_python_version',
        lambda: None,
    )
    monkeypatch.setattr(
        'sys.argv',
        ['run.py', '--config', str(cfg)],
    )
    main()
    assert os.environ.get('MONKEY_HEAD_CONFIG') == str(cfg)
