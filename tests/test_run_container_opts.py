# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Run Container Opts module (tests)

from run import main


def test_run_docker_compose(monkeypatch):
    called = {}

    def fake_manage():
        called["docker"] = True

    monkeypatch.setattr(
        "monkey_head.services.container_management.manage_containers", fake_manage
    )
    monkeypatch.setattr("monkey_head.core.system_checks.check_os_support", lambda: None)
    monkeypatch.setattr(
        "monkey_head.core.system_checks.check_python_version", lambda: None
    )
    monkeypatch.setattr("run.launch_gui", lambda: None)
    monkeypatch.setattr("run._load_cli", lambda: lambda: None)
    monkeypatch.setattr("sys.argv", ["run.py", "--docker-compose"])
    main()
    assert called.get("docker") is True


def test_run_kubernetes(monkeypatch):
    called = {}

    def fake_deploy():
        called["k8s"] = True

    monkeypatch.setattr(
        "monkey_head.services.container_management.deploy_kubernetes", fake_deploy
    )
    monkeypatch.setattr("monkey_head.core.system_checks.check_os_support", lambda: None)
    monkeypatch.setattr(
        "monkey_head.core.system_checks.check_python_version", lambda: None
    )
    monkeypatch.setattr("run.launch_gui", lambda: None)
    monkeypatch.setattr("run._load_cli", lambda: lambda: None)
    monkeypatch.setattr("sys.argv", ["run.py", "--kubernetes"])
    main()
    assert called.get("k8s") is True
