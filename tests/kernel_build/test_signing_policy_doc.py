"""Guard for kernel/huey-linux/signing-policy.md (Step 28).

The policy document is operator-facing prose. It must remain consistent with
the enforced behavior in `signing.py` (Step 18), `policy.py` (Step 5),
`verifier.py` (Step 19), and `release.py` (Step 20). These tests verify that
the document explicitly commits to each of those behaviors, so the doc
cannot silently drift away from the code.

The tests are intentionally textual rather than semantic. A future change to
the wording is fine as long as the required commitments remain explicit.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "kernel" / "huey-linux" / "signing-policy.md"


# ---------------------------------------------------------------------------
# File shape
# ---------------------------------------------------------------------------


def _read() -> str:
    assert DOC.is_file(), f"missing {DOC}"
    return DOC.read_text(encoding="utf-8")


def _lower() -> str:
    return _read().lower()


def _assert_contains_any(needles: tuple[str, ...], *, label: str) -> None:
    text = _lower().replace("**", "").replace("`", "")
    for needle in needles:
        if needle.lower() in text:
            return
    pytest.fail(
        f"{label}: none of {needles!r} found in {DOC.name}. "
        "The policy must explicitly state this commitment."
    )


def test_document_exists_and_is_nonempty() -> None:
    assert _read().strip()


def test_document_has_a_title() -> None:
    first_nonempty = next(
        line for line in _read().splitlines() if line.strip()
    )
    assert first_nonempty.startswith("# "), (
        f"signing-policy.md must start with a top-level heading, "
        f"got {first_nonempty!r}"
    )


# ---------------------------------------------------------------------------
# Commitment: keys never in Git
# ---------------------------------------------------------------------------


def test_states_keys_never_committed() -> None:
    _assert_contains_any(
        (
            "never be committed",
            "never committed",
            "never commit",
            "must never be committed",
        ),
        label="keys never in git",
    )


def test_states_key_locations_outside_repository() -> None:
    _assert_contains_any(
        (
            "outside the repository",
            "outside the working tree",
            "outside the repo",
        ),
        label="keys live outside repo",
    )


def test_lists_enforced_file_guards() -> None:
    """The doc must reference the automated guards that back the policy."""
    text = _lower()
    for guard in (".gitignore", "release.py", "signing.py"):
        assert guard in text, (
            f"signing-policy.md must mention the automated guard {guard!r}; "
            "the document is meant to reflect enforced behavior"
        )


# ---------------------------------------------------------------------------
# Commitment: MOK enrollment is manual
# ---------------------------------------------------------------------------


def test_states_mok_enrollment_is_manual() -> None:
    _assert_contains_any(
        (
            "manually by the operator",
            "performed manually",
            "is manual",
            "never automated",
            "not automated",
        ),
        label="MOK enrollment is manual",
    )


def test_documents_mokutil_import_command() -> None:
    text = _lower()
    assert "mokutil --import" in text, (
        "signing-policy.md must document the 'mokutil --import' command so "
        "the operator knows the exact procedure"
    )


def test_states_framework_never_runs_mokutil_import() -> None:
    _assert_contains_any(
        (
            "never runs `mokutil --import`",
            "never runs mokutil --import",
            "does not run",
            "does **not** run that command",
        ),
        label="framework never runs mokutil import",
    )


def test_references_human_runbook_step() -> None:
    text = _lower()
    assert "runbook" in text or "step 29" in text, (
        "signing-policy.md must point to the human-run install runbook for "
        "MOK enrollment and first-boot validation"
    )


# ---------------------------------------------------------------------------
# Commitment: unsigned modules are a blocking condition
# ---------------------------------------------------------------------------


def test_states_unsigned_required_module_blocks() -> None:
    _assert_contains_any(
        (
            "blocking",
            "boot_ready",
            "boot-ready",
        ),
        label="unsigned module blocks release",
    )


def test_states_boot_ready_false_on_unsigned() -> None:
    """The document must tie the failure to boot_ready=False explicitly."""
    text = _lower()
    assert "boot_ready" in text, (
        "signing-policy.md must explicitly reference boot_ready so the "
        "policy is clearly the prose counterpart of the enforced flag"
    )
    assert "false" in text, (
        "signing-policy.md must state that boot_ready is False when a "
        "required module is unsigned under Secure Boot"
    )


def test_states_wrong_key_is_critical() -> None:
    _assert_contains_any(
        (
            "critical",
            "signed by wrong key",
            "wrong key",
            "signed by a key",
        ),
        label="wrong-key signature is a critical finding",
    )


def test_lists_specific_finding_codes() -> None:
    """The doc should name the actionable finding codes an operator will see."""
    text = _lower()
    # At least one of these must be present so the operator can grep for it.
    expected_codes = (
        "required_module_unsigned",
        "module_signed_by_wrong_key",
    )
    assert any(code in text for code in expected_codes), (
        f"signing-policy.md must mention at least one of "
        f"{expected_codes!r} so the operator can map a failure to a rule"
    )


# ---------------------------------------------------------------------------
# Commitment: never disable Secure Boot
# ---------------------------------------------------------------------------


def test_states_never_disable_secure_boot() -> None:
    text = _lower()
    # Either an explicit statement or clear absence of any procedure that
    # would disable it.
    assert (
        "never" in text and "disable secure boot" in text
    ), (
        "signing-policy.md must state explicitly that the framework never "
        "disables Secure Boot and does not provide a procedure to do so"
    )


def test_does_not_contain_a_disable_secure_boot_procedure() -> None:
    """No imperative command that would disable Secure Boot appears as a step."""
    text = _read()
    # Reject command-like references such as `mokutil --disable-validation`
    # or `sbctl` disable instructions.
    forbidden_procedures = (
        r"mokutil\s+--disable-validation",
        r"\bsbctl\s+disable\b",
        r"\bdbxtool\s+--disable\b",
    )
    for pattern in forbidden_procedures:
        assert not re.search(pattern, text), (
            f"signing-policy.md must not provide a procedure to disable "
            f"Secure Boot (matched {pattern!r})"
        )


# ---------------------------------------------------------------------------
# Commitment: rotation and revocation are documented
# ---------------------------------------------------------------------------


def test_documents_key_rotation() -> None:
    text = _lower()
    assert "rotat" in text, (
        "signing-policy.md must document key rotation"
    )


def test_documents_revocation() -> None:
    text = _lower()
    assert "revoc" in text, (
        "signing-policy.md must document key revocation in case of compromise"
    )


# ---------------------------------------------------------------------------
# Commitment: passphrase handling
# ---------------------------------------------------------------------------


def test_states_pin_never_in_argv_or_logs() -> None:
    _assert_contains_any(
        (
            "never in argv",
            "never in a command-line log",
            "never printed",
            "never written",
            "never in argv, never in a command-line log",
        ),
        label="passphrase never in argv/logs",
    )


def test_mentions_kbuild_sign_pin() -> None:
    text = _lower()
    assert "kbuild_sign_pin" in text, (
        "signing-policy.md must name the KBUILD_SIGN_PIN environment "
        "variable that the signer uses for the passphrase"
    )


# ---------------------------------------------------------------------------
# Cross-reference integrity
# ---------------------------------------------------------------------------


def test_references_signing_module() -> None:
    assert "signing.py" in _lower()


def test_references_policy_module() -> None:
    assert "policy.py" in _lower()


def test_references_verifier_and_release() -> None:
    text = _lower()
    assert "verifier" in text
    assert "release" in text
