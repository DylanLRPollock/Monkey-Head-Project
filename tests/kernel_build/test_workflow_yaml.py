"""Guard for .github/workflows/huey-kernel-builder.yml (Step 30).

The workflow is the project's PR-safe continuous integration. Its safety
commitments are checked textually and structurally:

* triggers on `pull_request` and `push` to main only;
* never uses `pull_request_target`, `workflow_run`, `issue_comment`, or
  `issues` triggers;
* top-level `permissions` is exactly `contents: read`;
* no `secrets.*` reference anywhere;
* every `uses:` is pinned to a 40-char commit SHA with an optional
  `# vX.Y.Z` comment;
* the checkout step sets `persist-credentials: false`;
* `runs-on` names a GitHub-hosted runner, not `self-hosted`;
* no `sudo`, no `apt-get install`, no `pip install` from an untrusted index;
* no artifact upload matches `.ko`, `.run`, `.deb`, or `initramfs-*`;
* the workflow does not run any build that produces real artifacts.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "huey-kernel-builder.yml"


# ---------------------------------------------------------------------------
# YAML parsing
# ---------------------------------------------------------------------------


def _read() -> str:
    assert WORKFLOW.is_file(), f"missing {WORKFLOW}"
    return WORKFLOW.read_text(encoding="utf-8")


def _lower() -> str:
    """Inspect active YAML, excluding commentary and explanations."""
    return "\n".join(line for line in _read().splitlines() if not line.lstrip().startswith("#")).lower()


def _parse() -> dict:
    yaml = pytest.importorskip("yaml", reason="PyYAML required; added in Step 31")
    return yaml.safe_load(_read())


# ---------------------------------------------------------------------------
# File shape
# ---------------------------------------------------------------------------


def test_workflow_exists_and_is_nonempty() -> None:
    assert _read().strip()


def test_workflow_parses_as_yaml() -> None:
    _parse()  # will fail if not valid YAML


def test_workflow_has_a_name() -> None:
    assert "name:" in _read()


# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------


def test_trigger_is_pull_request_and_push() -> None:
    text = _lower()
    assert "pull_request:" in text
    assert "push:" in text


@pytest.mark.parametrize(
    "forbidden_trigger",
    [
        "pull_request_target:",
        "workflow_run:",
        "issue_comment:",
        "issues:",
    ],
)
def test_no_privileged_triggers(forbidden_trigger: str) -> None:
    """Privileged triggers must not be used: they are only safe for
    metadata-only tasks, and this workflow runs PR tests."""
    assert forbidden_trigger not in _lower(), (
        f"huey-kernel-builder.yml must not use {forbidden_trigger!r}; "
        "use pull_request (read-only token, no secrets) for CI"
    )


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


def test_top_level_permissions_is_contents_read() -> None:
    doc = _parse()
    perms = doc.get("permissions")
    assert perms == {"contents": "read"}, (
        "top-level permissions must be exactly {contents: read}; got "
        f"{perms!r}. Add per-job permissions only if justified in review."
    )


def test_no_write_permissions_anywhere() -> None:
    text = _lower()
    # Broad check: any "write" permission string is a red flag in this file.
    for pattern in (
        "contents: write",
        "pull-requests: write",
        "actions: write",
        "packages: write",
        "id-token: write",
        "security-events: write",
    ):
        assert pattern not in text, (
            f"huey-kernel-builder.yml must not grant {pattern!r}; the PR CI "
            "workflow is read-only"
        )


# ---------------------------------------------------------------------------
# Secrets
# ---------------------------------------------------------------------------


def test_no_secrets_reference() -> None:
    text = _lower()
    assert "secrets." not in text, (
        "huey-kernel-builder.yml must not reference repository secrets. "
        "Fork PRs would receive the empty string for every secret, and a "
        "same-repo PR from a compromised contributor could exfiltrate them."
    )


# ---------------------------------------------------------------------------
# Action pinning
# ---------------------------------------------------------------------------

_USES_RE = re.compile(r"^\s*-?\s*uses:\s*(\S+)(?:\s+#\s*(.+))?$", re.MULTILINE)
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


def _uses_entries() -> list[tuple[str, str | None]]:
    return [
        (m.group(1), m.group(2))
        for m in _USES_RE.finditer(_read())
    ]


def test_all_uses_are_pinned_to_full_sha() -> None:
    entries = _uses_entries()
    assert entries, "no uses: entries found; the workflow should run something"
    for ref, _comment in entries:
        if ref.startswith("./"):
            # Local composite actions and reusable workflows move with the
            # commit and are not pinned. Allowed.
            continue
        assert "@" in ref, f"uses entry without ref: {ref!r}"
        _owner_repo, sha = ref.rsplit("@", 1)
        assert _SHA40_RE.match(sha), (
            f"uses entry {ref!r} is not pinned to a full 40-char commit SHA"
        )


def test_every_pinned_action_has_a_version_comment() -> None:
    for ref, comment in _uses_entries():
        if ref.startswith("./"):
            continue
        assert comment and re.match(r"v\d+(\.\d+)*", comment.strip()), (
            f"uses entry {ref!r} is missing a '# vX.Y.Z' comment; add one so "
            "manual and automated reviewers know which release the SHA "
            "corresponds to"
        )


# ---------------------------------------------------------------------------
# Checkout hardening
# ---------------------------------------------------------------------------


def test_checkout_sets_persist_credentials_false() -> None:
    text = _read()
    assert "persist-credentials: false" in text, (
        "actions/checkout must set persist-credentials: false so the "
        "GITHUB_TOKEN is not left in .git/config for later PR-controlled steps"
    )


def test_checkout_fetches_depth_1() -> None:
    assert "fetch-depth: 1" in _read(), (
        "actions/checkout should fetch depth 1; there is no need for full "
        "history in this workflow"
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def test_runs_on_hosted_runner_only() -> None:
    text = _lower()
    assert "runs-on:" in text
    assert "ubuntu-24.04" in text or "ubuntu-latest" in text, (
        "the workflow must run on a GitHub-hosted Ubuntu runner; pin the "
        "version (ubuntu-24.04) so image changes are explicit"
    )
    assert "self-hosted" not in text, (
        "huey-kernel-builder.yml must not use a self-hosted runner. "
        "Public PRs can reach self-hosted runners and persist on them."
    )


# ---------------------------------------------------------------------------
# No privileged commands
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden",
    [
        "sudo ",
        "apt-get install",
        "apt install",
        "dnf install",
        "yum install",
        "pacman -S",
    ],
)
def test_no_privileged_package_installation(forbidden: str) -> None:
    assert forbidden not in _lower(), (
        f"huey-kernel-builder.yml must not contain {forbidden!r}; the "
        "workflow runs on a clean hosted image and installs only Python "
        "packages via pip from the checked-in pyproject.toml"
    )


def test_no_direct_pip_install_from_untrusted_index() -> None:
    """`pip install` is allowed only from the local project tree."""
    text = _read()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or "pip install" not in stripped:
            continue
        # Allowed: `pip install --upgrade pip`, `pip install -e ".[test]"`,
        # `pip install -e .`.
        allowed = (
            "--upgrade pip" in stripped
            or "-e ." in stripped
            or '-e ".[test]"' in stripped
        )
        assert allowed, (
            f"unexpected pip install invocation in workflow: {stripped!r}. "
            "This CI installs the project itself and its [test] extra; "
            "it must not install arbitrary packages from an index."
        )


# ---------------------------------------------------------------------------
# No real build steps
# ---------------------------------------------------------------------------


def test_no_real_build_commands() -> None:
    """`make`, `bindeb-pkg`, `mkinitramfs`, `sbsign`, `sign-file` must not run."""
    text = _read()
    forbidden = [
        " bindeb-pkg",
        "make -j",
        "mkinitramfs",
        "sbsign",
        "sign-file",
        "dpkg -i",
        "dkms install",
        "update-initramfs",
        "update-grub",
    ]
    for needle in forbidden:
        # Only consider matches in `run:` blocks (the comments describe what
        # is *not* done; those must be allowed).
        for block in _run_blocks():
            assert needle not in block, (
                f"huey-kernel-builder.yml must not run {needle!r}; the "
                "PR CI is limited to dry runs"
            )


def test_all_cli_build_invocations_use_dry_run() -> None:
    """Every build subcommand invocation must include --dry-run."""
    for block in _run_blocks():
        for match in re.finditer(
            r"huey\.kernel_build\.cli\s+"
            r"(config|build-kernel|build-nvidia|initramfs|sign|release)\b",
            block,
        ):
            sub = match.group(1)
            # Find the next line-boundary after the match and inspect the
            # whole command (up to the next blank line or continuation end).
            start = match.start()
            tail = block[start:]
            # A command ends at the first line that does not end with `\`
            # and is not part of a here-doc.
            lines = tail.splitlines()
            cmd_lines: list[str] = []
            for ln in lines:
                cmd_lines.append(ln)
                if not ln.rstrip().endswith("\\"):
                    break
            command = "\n".join(cmd_lines)
            assert "--dry-run" in command, (
                f"CLI subcommand {sub!r} is invoked without --dry-run in "
                f"this workflow. Full builds are a separate trusted workflow. "
                f"Offending command:\n{command}"
            )


def _run_blocks() -> list[str]:
    """Extract the contents of every run: block in the workflow.

    This is a small YAML-aware helper that avoids parsing the file twice
    with different libraries. It handles both `run: |` block scalars and
    `run: <single line>` forms.
    """
    text = _read()
    lines = text.splitlines()
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\s*)run:\s*(.*)$", line)
        if not m:
            i += 1
            continue
        indent = len(m.group(1))
        rest = m.group(2)
        if rest in ("|", "|-", ">", ">-"):
            i += 1
            body: list[str] = []
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip():
                    body.append("")
                    i += 1
                    continue
                nxt_indent = len(nxt) - len(nxt.lstrip())
                if nxt_indent <= indent:
                    break
                body.append(nxt)
                i += 1
            blocks.append("\n".join(body))
        else:
            blocks.append(rest)
            i += 1
    return blocks


# ---------------------------------------------------------------------------
# Artifact upload policy
# ---------------------------------------------------------------------------


def test_does_not_upload_binaries() -> None:
    """Artifact uploads must not match bootable or proprietary file types."""
    text = _read()
    # Only one upload step is expected; its path must be JSON/logs.
    for block in _run_blocks():
        assert "upload-artifact" not in block  # upload is a `uses:`, not `run:`
    # Check the upload-artifact step's `with:` inputs.
    m = re.search(
        r"upload-artifact.*?with:\s*\n((?:[ \t]+.*\n)+)",
        text,
        flags=re.DOTALL,
    )
    if m is None:
        pytest.skip("no upload-artifact step found; artifact policy is moot")
    inputs = m.group(1)
    for forbidden in (".ko", ".run", ".deb", "initramfs", "stage-", "vmlinuz"):
        assert forbidden not in inputs, (
            f"upload-artifact path or name matches {forbidden!r}; the PR CI "
            "must not publish build outputs"
        )


def test_upload_paths_are_only_json_and_logs() -> None:
    workflow = _parse()
    steps = workflow["jobs"]["ci"]["steps"]
    uploads = [step for step in steps if "upload-artifact@" in step.get("uses", "")]
    assert uploads, "Expected upload-artifact for dry-run logs"
    for step in uploads:
        paths = step.get("with", {}).get("path", "").splitlines()
        paths = [path.strip() for path in paths if path.strip()]
        assert paths, "upload-artifact has no path entries"
        assert all(any(pat in path for pat in (".json", ".log", ".txt")) for path in paths)
        assert all(not any(ext in path for ext in (".ko", ".run", ".deb", "initramfs", "vmlinuz")) for path in paths)


# ---------------------------------------------------------------------------
# Additional safety guards
# ---------------------------------------------------------------------------


def test_no_self_hosted_runner_labels() -> None:
    assert "self-hosted" not in _lower()


def test_no_container_or_service_with_untrusted_image() -> None:
    """This workflow runs in the default GitHub-hosted VM only."""
    text = _read()
    assert "container:" not in text, (
        "huey-kernel-builder.yml must not declare a container. It runs in "
        "the default ubuntu-24.04 hosted VM."
    )


def test_does_not_interpolate_untrusted_event_data_into_run() -> None:
    """No ${{ github.event.* }} may appear inside run: blocks."""
    for block in _run_blocks():
        if "${{" not in block:
            continue
        for m in re.finditer(r"\$\{\{\s*([^}]+)\}\}", block):
            expr = m.group(1).strip()
            # Allow the safe, framework-controlled expressions only.
            safe_prefixes = (
                "github.ref",
                "github.event_name",
                "github.event.pull_request.base.ref",
                "github.workflow",
                "github.sha",
            )
            if any(expr.startswith(p) for p in safe_prefixes):
                continue
            pytest.fail(
                f"run: block interpolates {{{{ {expr} }}}} which can be "
                "attacker-controlled. Pass it through an env: variable or "
                "use actions/github-script instead."
            )
