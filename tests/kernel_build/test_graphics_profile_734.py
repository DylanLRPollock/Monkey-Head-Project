"""Static regression checks for the staged 7.3.4 Intel-display handover.

These assertions are not a substitute for hardware/firmware/Wayland
qualification. They prevent accidental premature AMDGPU removal and Nouveau
enablement in the initial V100 build profile.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILES = ROOT / "kernel" / "huey-linux" / "profiles"


def test_testing1_keeps_recovery_gpu_drivers() -> None:
    cfg = (PROFILES / "v100-workstation.config").read_text(encoding="utf-8")
    assert 'CONFIG_LOCALVERSION=""' in cfg
    assert "# CONFIG_LOCALVERSION_AUTO is not set" in cfg
    assert "CONFIG_DRM_I915=m" in cfg
    assert "CONFIG_DRM_AMDGPU=m" in cfg
    assert "# CONFIG_DRM_NOUVEAU is not set" in cfg


def test_intel_only_fragment_is_explicitly_opt_in() -> None:
    cfg = (PROFILES / "intel-primary-v100-only.config").read_text(
        encoding="utf-8"
    )
    assert "Do NOT merge this into the first testing1 build" in cfg
    assert "CONFIG_DRM_I915=m" in cfg
    assert "# CONFIG_DRM_AMDGPU is not set" in cfg
    assert "# CONFIG_DRM_NOUVEAU is not set" in cfg


def test_build_intent_uses_testing1_upstream_base() -> None:
    cfg = (ROOT / "kernel" / "huey-linux" / "build.yaml").read_text(
        encoding="utf-8"
    )
    assert "source_type: upstream" in cfg
    assert 'version: "7.3.4"' in cfg
    assert 'localversion: "-huey-testing1"' in cfg
    assert "module_flavor: proprietary" in cfg
