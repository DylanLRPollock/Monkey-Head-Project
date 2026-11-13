"""Guard for kernel/huey-linux/initramfs/modprobe.d/huey-v100.conf (Step 16).

This is a static data file consumed by the install runbook (Step 29) and
staged by the initramfs builder (Step 17). It must:

- exclude Nouveau from claiming the V100 (both `blacklist nouveau` and the
  stronger `install nouveau /bin/false`, plus `options nouveau modeset=0`);
- leave AMDGPU untouched (RX 570 display path);
- leave the proprietary NVIDIA modules untouched (V100 compute path);
- invent no `options nvidia ...` values;
- document that it is installed only by the runbook, not by any build.

All tests run offline and perform no host mutation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONF = (
    REPO_ROOT
    / "kernel"
    / "huey-linux"
    / "initramfs"
    / "modprobe.d"
    / "huey-v100.conf"
)

_COMMENT_LINE = re.compile(r"^\s*#")
_BLACKLIST_RE = re.compile(r"^\s*blacklist\s+(\S+)")
_INSTALL_RE = re.compile(r"^\s*install\s+(\S+)\s+(\S+)")
_OPTIONS_RE = re.compile(r"^\s*options\s+(\S+)")


def _read() -> str:
    assert CONF.is_file(), f"missing {CONF}"
    return CONF.read_text(encoding="utf-8")


def _active_lines() -> list[str]:
    """Return non-blank, non-comment lines, stripped."""
    result: list[str] = []
    for raw in _read().splitlines():
        s = raw.strip()
        if not s or _COMMENT_LINE.match(s):
            continue
        result.append(s)
    return result


def _blacklisted_modules() -> set[str]:
    return {
        m.group(1)
        for line in _active_lines()
        if (m := _BLACKLIST_RE.match(line))
    }


def _installed_modules() -> dict[str, str]:
    return {
        m.group(1): m.group(2)
        for line in _active_lines()
        if (m := _INSTALL_RE.match(line))
    }


def _modules_with_options() -> set[str]:
    return {
        m.group(1)
        for line in _active_lines()
        if (m := _OPTIONS_RE.match(line))
    }


def _comment_text() -> str:
    return "\n".join(
        raw.strip()
        for raw in _read().splitlines()
        if _COMMENT_LINE.match(raw.strip())
    )


# ---------------------------------------------------------------------------
# File shape
# ---------------------------------------------------------------------------


def test_conf_exists_and_is_nonempty() -> None:
    assert _read().strip()


def test_every_active_line_is_a_known_modprobe_directive() -> None:
    for line in _active_lines():
        assert (
            _BLACKLIST_RE.match(line)
            or _INSTALL_RE.match(line)
            or _OPTIONS_RE.match(line)
        ), (
            f"unrecognized directive in modprobe conf: {line!r}. "
            "Expected blacklist/install/options."
        )


# ---------------------------------------------------------------------------
# Nouveau exclusion (defense in depth)
# ---------------------------------------------------------------------------


def test_nouveau_is_blacklisted() -> None:
    assert "nouveau" in _blacklisted_modules(), (
        "huey-v100.conf must contain 'blacklist nouveau' so that aliases "
        "and udev cannot automatically load Nouveau and claim the V100"
    )


def test_nouveau_install_rejects_explicit_modprobe() -> None:
    """blacklist alone does not stop an explicit modprobe; install does."""
    installed = _installed_modules()
    assert installed.get("nouveau") == "/bin/false", (
        "huey-v100.conf must contain 'install nouveau /bin/false'. "
        "modprobe.d(5) documents that 'blacklist' suppresses automatic "
        "loading but does not block an explicit 'modprobe nouveau'; "
        "'install ... /bin/false' is required for that stronger guarantee"
    )


def test_nouveau_modeset_disabled() -> None:
    assert "nouveau" in _modules_with_options(), (
        "huey-v100.conf must contain 'options nouveau modeset=0' as the "
        "NVIDIA-documented fallback so Nouveau cannot drive modesetting "
        "even if the module were somehow present"
    )


# ---------------------------------------------------------------------------
# AMDGPU must remain loadable
# ---------------------------------------------------------------------------


def test_amdgpu_is_not_blacklisted() -> None:
    assert "amdgpu" not in _blacklisted_modules(), (
        "amdgpu must NOT be blacklisted: the AMD RX 570 is the display GPU"
    )


def test_amdgpu_is_not_blocked_by_install() -> None:
    assert "amdgpu" not in _installed_modules(), (
        "amdgpu must not be paired with an 'install ... /bin/false' rule; "
        "that would block the RX 570 display path"
    )


# ---------------------------------------------------------------------------
# Proprietary NVIDIA modules must remain loadable
# ---------------------------------------------------------------------------


def test_nvidia_modules_are_not_blacklisted() -> None:
    for mod in ("nvidia", "nvidia-uvm", "nvidia-modeset", "nvidia-drm"):
        assert mod not in _blacklisted_modules(), (
            f"{mod!r} must not be blacklisted: it belongs to the proprietary "
            "V100 compute path (or may be needed by a future display profile)"
        )


def test_nvidia_modules_are_not_blocked_by_install() -> None:
    installed = _installed_modules()
    for mod in ("nvidia", "nvidia-uvm", "nvidia-modeset", "nvidia-drm"):
        assert mod not in installed, (
            f"{mod!r} must not have an 'install ... /bin/false' rule"
        )


# ---------------------------------------------------------------------------
# No invented NVIDIA options
# ---------------------------------------------------------------------------


def test_no_nvidia_options_are_invented() -> None:
    """`options nvidia ...` must not be present without documented provenance."""
    options_for = _modules_with_options()
    for mod in ("nvidia", "nvidia-uvm", "nvidia-modeset", "nvidia-drm"):
        assert mod not in options_for, (
            f"'options {mod} ...' is present. Specific NVreg_* options "
            "must be documented by the 580.196.07 branch for this exact "
            "workload and added in a separate reviewed change with "
            "provenance. Do not invent options here."
        )


# ---------------------------------------------------------------------------
# Installation contract
# ---------------------------------------------------------------------------


def test_installation_is_documented_as_runbook_only() -> None:
    """The file must state it is installed by the runbook, not by a build."""
    comments = _comment_text().lower()
    assert "runbook" in comments or "huey-kernel-upgrade" in comments, (
        "huey-v100.conf must document that it is installed only by the "
        "human-approved runbook (Step 29), not by any build or CI step"
    )
    assert "not installed by any build" in comments, (
        "huey-v100.conf must explicitly state that no build or CI step "
        "installs it to /etc/modprobe.d/"
    )


def test_references_the_profile_fragment_for_nouveau_disabled() -> None:
    """The defense-in-depth rationale must reference the kernel config decision."""
    comments = _comment_text().lower()
    assert "v100-workstation.config" in comments or "config_drm_nouveau" in comments, (
        "The Nouveau defense-in-depth rationale must reference the profile "
        "fragment that disables CONFIG_DRM_NOUVEAU, so a future reader sees "
        "why the modprobe rules are redundant-but-kept"
    )
