# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Hostos Module module (tests)

import importlib.util
from pathlib import Path
from unittest.mock import patch

HOSTOS_MODULE = (
    Path(__file__).resolve().parents[1] / "docker" / "hostos" / "hostos.py"
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
