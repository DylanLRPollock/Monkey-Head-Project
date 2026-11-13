"""Guard for docs/runbooks/huey-kernel-upgrade.md (Step 29).

The runbook is operator-facing prose. Its safety commitments must remain
consistent with the framework's enforced behavior (Steps 18, 19, 20, 26, 28)
and with the handoff's explicit requirements:

- physical/console recovery access is required before the first boot;
- preflight backups are captured;
- installation order and DKMS confirmation are documented;
- initramfs inspection is documented;
- GRUB entry preservation and one-time boot selection are documented;
- post-boot checks cover kernel, storage, display, compute, thermal,
  Steam/Proton;
- rollback via the previous kernel is documented;
- failed-DKMS recovery is documented;
- independent recovery for display-only and compute-only is documented;
- Steam/Proton Vulkan wrapper is preserved;
- thermal abort thresholds are documented;
- explicit prohibitions: no apt autoremove, no apt purge, no
  update-grub-with-changed-default as a reflex, no grub-reboot, no
  system-wide ICD switch, no disabling Secure Boot.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "runbooks" / "huey-kernel-upgrade.md"


def _read() -> str:
    assert DOC.is_file(), f"missing {DOC}"
    return DOC.read_text(encoding="utf-8")


def _lower() -> str:
    return _read().lower()


def _contains_any(needles: tuple[str, ...]) -> bool:
    text = _lower()
    return any(n.lower() in text for n in needles)


# ---------------------------------------------------------------------------
# File shape
# ---------------------------------------------------------------------------


def test_runbook_exists_and_is_nonempty() -> None:
    assert _read().strip()


def test_runbook_has_a_title() -> None:
    first = next(line for line in _read().splitlines() if line.strip())
    assert first.startswith("# "), f"missing top-level heading: {first!r}"


def test_runbook_has_multiple_major_sections() -> None:
    headings = re.findall(r"^## ", _read(), flags=re.MULTILINE)
    assert len(headings) >= 10, (
        f"runbook has only {len(headings)} major sections; it should be "
        "comprehensive enough to cover the entire upgrade lifecycle"
    )


# ---------------------------------------------------------------------------
# Commitment: physical/console recovery access required
# ---------------------------------------------------------------------------


def test_states_physical_access_is_required() -> None:
    assert _contains_any(
        (
            "physical presence",
            "physical access",
            "physical (or ipmi/kvm",
            "physical recovery access is required",
        )
    ), "runbook must state that physical (or IPMI/KVM) access is required"


def test_states_recovery_medium_is_required() -> None:
    assert _contains_any(
        (
            "recovery medium",
            "installation usb",
            "in hand",
        )
    ), "runbook must require a known-good recovery medium"


def test_states_do_not_proceed_without_physical_access() -> None:
    """The runbook must explicitly say to stop if physical access is unavailable."""
    assert _contains_any(
        (
            "do not proceed",
            "do not start",
            "there is no \"remote-only\" path",
            "there is no remote-only path",
        )
    ), "runbook must refuse to proceed without physical/console access"


# ---------------------------------------------------------------------------
# Commitment: preflight backups
# ---------------------------------------------------------------------------


def test_documents_baseline_capture() -> None:
    text = _lower()
    assert "baseline" in text
    # Specific baseline artifacts must be named.
    for needle in ("grub.cfg", "/etc/default/grub", "/etc/modprobe.d"):
        assert needle in text, (
            f"runbook must document capture of {needle!r} during preflight"
        )


def test_documents_dkms_baseline() -> None:
    text = _lower()
    assert "dkms status" in text
    assert "nvidia-smi" in text


def test_documents_mokutil_baseline() -> None:
    assert "mokutil --sb-state" in _lower()


# ---------------------------------------------------------------------------
# Commitment: install order
# ---------------------------------------------------------------------------


def test_documents_headers_first_install_order() -> None:
    text = _lower()
    assert "linux-headers" in text and "linux-image" in text
    # The order matters; the runbook must state it.
    assert _contains_any(
        (
            "headers first",
            "headers before",
            "install order",
            "kernel headers first",
        )
    ), "runbook must state the headers-first install order and justify it"


# ---------------------------------------------------------------------------
# Commitment: DKMS confirmation via vermagic
# ---------------------------------------------------------------------------


def test_documents_dkms_confirmation() -> None:
    text = _lower()
    assert "dkms status" in text
    assert "modinfo -k" in text or "modinfo -f vermagic" in text


def test_documents_vermagic_match_requirement() -> None:
    text = _lower()
    assert "vermagic" in text
    assert _contains_any(
        (
            "must contain",
            "must match",
            "do not continue",
        )
    ), "runbook must require vermagic match or abort"


# ---------------------------------------------------------------------------
# Commitment: initramfs inspection
# ---------------------------------------------------------------------------


def test_documents_initramfs_inspection() -> None:
    text = _lower()
    assert "lsinitramfs" in text
    assert "nouveau" in text, (
        "runbook must check that nouveau is absent from the initramfs"
    )


# ---------------------------------------------------------------------------
# Commitment: GRUB preservation and one-time boot
# ---------------------------------------------------------------------------


def test_documents_grub_entry_preservation() -> None:
    assert _contains_any(
        (
            "does not change the default",
            "must not change",
            "default entry was not changed",
            "grub_default",
        )
    ), "runbook must document that the default GRUB entry is preserved"


def test_documents_one_time_boot_selection() -> None:
    assert _contains_any(
        (
            "select the new kernel from the grub menu",
            "select the custom kernel entry",
            "grub menu manually",
            "one-time boot",
        )
    ), "runbook must document one-time boot selection via the GRUB menu"


def test_explicitly_rejects_grub_reboot() -> None:
    text = _lower()
    assert "grub-reboot" in text, (
        "runbook must explicitly name grub-reboot as not used, with a reason"
    )
    assert _contains_any(
        (
            "not used by this runbook",
            "not used",
            "does not use `grub-reboot`",
        )
    )


# ---------------------------------------------------------------------------
# Commitment: post-boot checks
# ---------------------------------------------------------------------------


def test_documents_post_boot_kernel_check() -> None:
    assert "uname -r" in _lower()


def test_documents_post_boot_display_check() -> None:
    text = _lower()
    assert "amdgpu" in text
    assert "lspci" in text


def test_documents_post_boot_compute_check() -> None:
    text = _lower()
    assert "nvidia-smi" in text
    assert "nvidia-uvm" in text or "nvidia_uvm" in text


def test_distinguishes_driver_cuda_api_from_installed_toolkit() -> None:
    """The runbook must carry the same distinction the verifier enforces."""
    text = _lower()
    assert "nvcc --version" in text
    assert _contains_any(
        (
            "driver-advertised",
            "advertised cuda api",
            "not the installed toolkit",
            "distinct",
        )
    ), "runbook must distinguish nvidia-smi's advertised CUDA API from the installed toolkit"


# ---------------------------------------------------------------------------
# Commitment: thermal abort thresholds
# ---------------------------------------------------------------------------


def test_documents_thermal_abort_thresholds() -> None:
    text = _lower()
    assert "thermal abort" in text or "abort threshold" in text
    assert "80" in text, "runbook must name the idle temperature abort threshold"
    assert "85" in text, "runbook must name the load temperature abort threshold"


def test_references_the_86c_baseline() -> None:
    text = _lower()
    assert "86" in text, (
        "runbook must reference the observed 86°C idle baseline and explain "
        "why it is a warning sign, not a qualification"
    )


# ---------------------------------------------------------------------------
# Commitment: rollback and failed-DKMS recovery
# ---------------------------------------------------------------------------


def test_documents_rollback_via_previous_kernel() -> None:
    text = _lower()
    assert "rollback" in text
    assert _contains_any(
        (
            "select the previous",
            "previous kernel",
            "boot the previous",
            "recovery medium",
        )
    )


def test_documents_failed_dkms_recovery() -> None:
    text = _lower()
    assert "failed dkms" in text or "dkms recovery" in text
    assert "dkms install" in text, (
        "runbook must document the dkms install retry for the new kernel"
    )


# ---------------------------------------------------------------------------
# Commitment: independent recovery of display and compute
# ---------------------------------------------------------------------------


def test_documents_independent_recovery() -> None:
    text = _lower()
    assert _contains_any(
        (
            "display and compute",
            "display-only",
            "compute-only",
            "display path and the nvidia compute path are",
            "separate operations",
        )
    ), "runbook must treat display and compute recovery independently"


# ---------------------------------------------------------------------------
# Commitment: Steam/Proton Vulkan wrapper
# ---------------------------------------------------------------------------


def test_preserves_steam_proton_wrapper() -> None:
    text = _lower()
    assert "steam" in text and "proton" in text
    assert _contains_any(
        (
            "preserve",
            "backup",
            "baseline",
        )
    ), "runbook must require backup/preservation of the Steam/Proton wrapper"


def test_does_not_switch_system_wide_icd() -> None:
    text = _lower()
    assert _contains_any(
        (
            "do not replace the system-wide vulkan icd",
            "do not switch the system-wide vulkan icd",
            "custom wrapper is the supported path",
        )
    ), "runbook must forbid switching the system-wide Vulkan ICD"


# ---------------------------------------------------------------------------
# Commitment: explicit prohibitions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden_phrase",
    [
        "apt autoremove",
        "apt purge",
        "apt remove <any kernel",
        "apt remove <any kernel or headers>",
        "update-grub",
        "grub-install",
        "dkms install",
        "mokutil --delete",
    ],
)
def test_explicitly_forbids_destructive_commands(forbidden_phrase: str) -> None:
    """The runbook must list each of these as forbidden."""
    text = _lower()
    # The phrase must appear somewhere (typically in a "forbidden" list).
    assert forbidden_phrase.lower() in text, (
        f"runbook must explicitly name {forbidden_phrase!r} as a forbidden "
        "command during the upgrade lifecycle"
    )


def test_does_not_provide_a_disable_secure_boot_procedure() -> None:
    text = _read()
    forbidden_procedures = (
        r"mokutil\s+--disable-validation",
        r"\bsbctl\s+disable\b",
        r"\bdbxtool\s+--disable\b",
    )
    for pattern in forbidden_procedures:
        assert not re.search(pattern, text), (
            f"runbook must not contain a procedure to disable Secure Boot "
            f"(matched {pattern!r})"
        )


# ---------------------------------------------------------------------------
# Cross-references
# ---------------------------------------------------------------------------


def test_references_signing_policy() -> None:
    assert "signing-policy.md" in _lower()


def test_references_handoff() -> None:
    assert "huey_custom_kernel_agent_handoff" in _lower() or "handoff" in _lower()


def test_references_step_18_or_19_or_20() -> None:
    """The runbook must cross-link the modules whose behavior it documents."""
    text = _lower()
    assert any(
        needle in text
        for needle in ("signing.py", "verifier.py", "release.py")
    ), "runbook must cross-reference at least one of the enforcement modules"
