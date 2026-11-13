"""Guard for kernel/huey-linux/initramfs/modules.list (Step 15).

This is a static data file consumed by Step 17 (initramfs_builder). Its
runtime acceptance criterion -- "checked against actual staged module
names and dependencies; clear failures for unavailable requested modules"
-- is enforced by Step 17's integration test, not here.

This file verifies the static properties that must hold for Step 17 to
be able to do its job:

- the file exists and parses as initramfs-tools format;
- amdgpu is listed (RX 570 display path must not be broken);
- nvidia and nvidia-uvm are listed (compute readiness);
- nvidia-modeset and nvidia-drm are NOT listed (V100 has no display);
- amdgpu is not blacklisted here (blacklists belong in modprobe.d);
- no hand-rolled dependency hacks are listed (modprobe resolves deps);
- the rationale for the inclusion and exclusion decisions is documented.

All tests run offline and perform no host mutation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULES_LIST = REPO_ROOT / "kernel" / "huey-linux" / "initramfs" / "modules.list"

_COMMENT_LINE = re.compile(r"^\s*#")
_MODULE_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")

# Core kernel modules that modprobe resolves automatically and that must
# not be hand-listed to "help" dependency resolution. If one of these is
# genuinely needed early (e.g. for a future storage config change), it
# needs its own reviewed addition with a comment explaining why, and this
# deny-list must be updated in the same change.
_DENY_AS_DEPENDENCY_HACK = frozenset(
    {
        "drm",
        "drm_kms_helper",
        "i2c-core",
        "i2c-algo-bit",
    }
)

# The expected active module set for the v100-workstation profile.
_EXPECTED_MODULES = frozenset({"amdgpu", "nvidia", "nvidia-uvm"})


def _read() -> str:
    assert MODULES_LIST.is_file(), f"missing {MODULES_LIST}"
    return MODULES_LIST.read_text(encoding="utf-8")


def _active_lines() -> list[str]:
    """Return the non-blank, non-comment lines of the file, in order."""
    result: list[str] = []
    for raw in _read().splitlines():
        stripped = raw.strip()
        if not stripped or _COMMENT_LINE.match(stripped):
            continue
        result.append(stripped)
    return result


def _active_module_names() -> list[str]:
    """Return the module-name token of each active line, in order."""
    return [line.split(None, 1)[0] for line in _active_lines()]


def _comment_text() -> str:
    return "\n".join(
        raw.strip() for raw in _read().splitlines() if _COMMENT_LINE.match(raw.strip())
    )


# ---------------------------------------------------------------------------
# File presence and format
# ---------------------------------------------------------------------------


def test_modules_list_exists_and_is_nonempty() -> None:
    assert _read().strip()


def test_active_lines_have_plausible_module_names() -> None:
    """Every non-comment line must start with a lowercase module name."""
    for line in _active_lines():
        name = line.split(None, 1)[0]
        assert _MODULE_NAME_RE.match(name), (
            f"line {line!r} does not start with a plausible module name "
            f"(expected lowercase [a-z0-9_]+); got {name!r}"
        )


def test_no_duplicate_modules() -> None:
    names = _active_module_names()
    assert len(names) == len(set(names)), (
        f"duplicate module entries in modules.list: {names}"
    )


# ---------------------------------------------------------------------------
# Required inclusions
# ---------------------------------------------------------------------------


def test_amdgpu_is_listed() -> None:
    """The RX 570 display path must be present in the initramfs."""
    assert "amdgpu" in _active_module_names(), (
        "modules.list must include 'amdgpu' so the RX 570 display path is "
        "available from the initramfs"
    )


def test_nvidia_is_listed() -> None:
    assert "nvidia" in _active_module_names(), (
        "modules.list must include the proprietary 'nvidia' module for "
        "the V100 compute path"
    )


def test_nvidia_uvm_is_listed() -> None:
    assert "nvidia-uvm" in _active_module_names(), (
        "modules.list must include 'nvidia-uvm'; CUDA Unified Memory and "
        "several ML frameworks require it, and it must be present in the "
        "initramfs for compute readiness"
    )


# ---------------------------------------------------------------------------
# Required exclusions
# ---------------------------------------------------------------------------


def test_nvidia_modeset_not_listed() -> None:
    """nvidia-modeset is conditional; the V100 has no display output."""
    assert "nvidia-modeset" not in _active_module_names(), (
        "nvidia-modeset must not be in modules.list for the v100-workstation "
        "profile: the Tesla V100 has no display output, so modesetting is "
        "unnecessary in the initramfs. Add it only in a display-bearing "
        "profile's modules.list."
    )


def test_nvidia_drm_not_listed() -> None:
    """nvidia-drm is conditional; same rationale as nvidia-modeset."""
    assert "nvidia-drm" not in _active_module_names(), (
        "nvidia-drm must not be in modules.list for the v100-workstation "
        "profile: the Tesla V100 has no display output, so DRM/KMS "
        "integration is unnecessary in the initramfs."
    )


# ---------------------------------------------------------------------------
# No blacklists here
# ---------------------------------------------------------------------------


def test_no_blacklist_directives() -> None:
    """Blacklist directives belong in modprobe.d, not in modules.list."""
    text = _read().lower()
    # Reject anything that looks like 'blacklist foo' in an active line.
    for line in _active_lines():
        lowered = line.lower()
        assert "blacklist" not in lowered, (
            f"'blacklist' must not appear as an active line in modules.list "
            f"(got {line!r}). Blacklists belong in modprobe.d/"
            "huey-v100.conf (Step 16)."
        )
    # And it must not appear even in comments as if it were a directive.
    assert "blacklist amdgpu" not in text, (
        "amdgpu must never be described as blacklisted in modules.list; "
        "the RX 570 display path is intentionally kept enabled"
    )


# ---------------------------------------------------------------------------
# No dependency hacks
# ---------------------------------------------------------------------------


def test_no_hand_rolled_dependency_hacks() -> None:
    """modprobe resolves dependencies; do not hand-list core modules."""
    names = set(_active_module_names())
    overlap = names & _DENY_AS_DEPENDENCY_HACK
    assert not overlap, (
        f"modules.list lists core dependency modules {sorted(overlap)} that "
        "modprobe resolves automatically. Do not add a module solely to "
        "satisfy another module's dependency."
    )


# ---------------------------------------------------------------------------
# Expected module set (exact)
# ---------------------------------------------------------------------------


def test_active_set_matches_expected_profile_modules() -> None:
    """Guard against accidental additions without a reviewed change.

    If a future contributor genuinely needs to add a module for a new
    requirement, this test should be updated in the same change together
    with a comment in modules.list explaining why. That is intentional:
    the initramfs contents should be a deliberate, reviewed decision.
    """
    actual = set(_active_module_names())
    assert actual == _EXPECTED_MODULES, (
        f"active module set drifted from the reviewed set.\n"
        f"  expected: {sorted(_EXPECTED_MODULES)}\n"
        f"  actual:   {sorted(actual)}\n"
        f"  missing:  {sorted(_EXPECTED_MODULES - actual)}\n"
        f"  extra:    {sorted(actual - _EXPECTED_MODULES)}\n"
        "If the extra module is intentional, update this test and add a "
        "comment in modules.list explaining the reason."
    )


# ---------------------------------------------------------------------------
# Rationale comments must be present
# ---------------------------------------------------------------------------


def test_amdgpu_rationale_present() -> None:
    """The amdgpu entry must explain the display path."""
    comments = _comment_text().lower()
    assert "amdgpu" in comments, (
        "modules.list must explain why amdgpu is included "
        "(RX 570 display path)"
    )
    assert "display" in comments or "rx 570" in comments, (
        "the amdgpu rationale must mention the display/RX 570 role"
    )


def test_nvidia_modeset_and_drm_exclusion_rationale_present() -> None:
    """The exclusions of modeset/drm must be documented with a reason."""
    comments = _comment_text().lower()
    assert "nvidia-modeset" in comments, (
        "modules.list must explain why nvidia-modeset is not included"
    )
    assert "nvidia-drm" in comments, (
        "modules.list must explain why nvidia-drm is not included"
    )
    # Combined rationale: both refer to the V100's lack of display output.
    assert (
        "no display" in comments
        or "no display output" in comments
        or "headless" in comments
    ), (
        "the exclusion rationale must state that the V100 has no display "
        "output"
    )
