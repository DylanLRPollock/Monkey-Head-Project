# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Hostos Module module (tests)

import importlib.util
from pathlib import Path
from unittest.mock import patch

HOSTOS_MODULE = (
    Path(__file__).resolve().parents[1] / "infra" / "docker" / "docker" / "hostos" / "hostos.py"
)
spec = importlib.util.spec_from_file_location("hostos_module", HOSTOS_MODULE)
HostOS = importlib.util.module_from_spec(spec)
assert spec and spec.loader  # defensive for mypy/static analyzers
spec.loader.exec_module(HostOS)

enable_services = HostOS.enable_services
check_virtualization = HostOS.check_virtualization
configure_firewall = HostOS.configure_firewall


class DummyCompleted:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_enable_services():
    with (
        patch("orchestrator_utils.shutil.which", return_value=True),
        patch("orchestrator_utils.run", return_value=DummyCompleted()),
    ):
        enable_services()


def test_check_virtualization():
    with (
        patch("orchestrator_utils._detect_cpu_flags", return_value={"vmx", "svm"}),
        patch("orchestrator_utils.Path.exists", return_value=True),
        patch(
            "orchestrator_utils._probe_virtualization_environment",
            return_value="bare-metal",
        ),
    ):
        check_virtualization()


def test_configure_firewall():
    with (
        patch("orchestrator_utils.shutil.which", return_value=True),
        patch(
            "orchestrator_utils.run",
            return_value=DummyCompleted(stdout="Status: active"),
        ),
    ):
        configure_firewall(1234)


def test_enable_services_logs_usermod_failure(caplog):
    with (
        patch("orchestrator_utils.shutil.which", return_value=True),
        patch(
            "orchestrator_utils.run",
            side_effect=[DummyCompleted(), OSError("no login")],
        ),
        caplog.at_level("WARNING"),
    ):
        enable_services()
    assert "Unable to add current user to docker group" in caplog.text


def test_system_requirements_ping_failure_then_success(caplog):
    with (
        patch("orchestrator_utils.shutil.disk_usage") as mock_usage,
        patch("orchestrator_utils.run") as mock_run,
        caplog.at_level("WARNING"),
    ):
        mock_usage.return_value = type("U", (), {"free": 10 * (1024**3)})()
        mock_run.side_effect = [OSError("ping missing"), DummyCompleted(returncode=0)]

        HostOS.ensure_system_requirements(logger=HostOS.log, ping_hosts=("a", "b"))

    assert "Ping to a failed" in caplog.text
