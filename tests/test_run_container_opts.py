# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Run Container Opts module (tests)

from huey.memory.PY.run import main


def test_run_docker_compose(monkeypatch):
    called = {}

    def fake_manage(**kwargs):
        called["docker"] = kwargs

    monkeypatch.setattr(
        "huey.os.services.container_management.manage_containers", fake_manage
    )
    monkeypatch.setattr("huey.os.core.system_checks.check_os_support", lambda: None)
    monkeypatch.setattr("huey.os.core.system_checks.check_python_version", lambda: None)
    monkeypatch.setattr("huey.memory.PY.run.launch_gui", lambda: None)
    monkeypatch.setattr("huey.memory.PY.run._load_cli", lambda: lambda: None)
    monkeypatch.setattr("sys.argv", ["run.py", "--docker-compose", "--yes"])
    main()
    assert called["docker"] == {
        "confirmed": True,
        "actor_role": "operator",
        "dry_run": False,
    }


def test_run_kubernetes(monkeypatch):
    called = {}

    def fake_deploy(**kwargs):
        called["k8s"] = kwargs

    monkeypatch.setattr(
        "huey.os.services.container_management.deploy_kubernetes", fake_deploy
    )
    monkeypatch.setattr("huey.os.core.system_checks.check_os_support", lambda: None)
    monkeypatch.setattr("huey.os.core.system_checks.check_python_version", lambda: None)
    monkeypatch.setattr("run.launch_gui", lambda: None)
    monkeypatch.setattr("run._load_cli", lambda: lambda: None)
    monkeypatch.setattr("sys.argv", ["run.py", "--kubernetes", "--yes"])
    main()
    assert called["k8s"] == {
        "confirmed": True,
        "actor_role": "operator",
        "dry_run": False,
    }
