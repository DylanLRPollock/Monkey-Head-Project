<!--
# ---------------------------------------------------------------------------
# Monkey-Head-Project
# Component: Repository / GitHub Actions Pin Registry
# Author: Dylan L.R. Pollock
# Documentation: https://www.dlrp.ca
#
# Philosophy: Breathing new life into old tech.
# ---------------------------------------------------------------------------
-->

# GitHub Actions Security: Pin Registry

This file records **why** each third-party action in `.github/workflows/` is
pinned to a specific commit, and **how** to update those pins safely. It is
the companion document to the workflow files themselves — the workflows hold
the pins, this file holds the rationale.

> **Rule of thumb.** If you cannot explain why an action is pinned to a
> specific commit, it should not be in a workflow. Add it here first.

---

## Policy

### 1. Immutable references only

Every third-party action is referenced by a **full 40-character commit SHA**,
never by a tag or branch. Tags are mutable: `@v4` today can point to a
different commit tomorrow if the upstream maintainer force-pushes or re-tags.
A SHA cannot change.

```yaml
# Correct
- uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd  # v6

# Incorrect -- mutable, and Dependabot cannot audit the change
- uses: actions/checkout@v6
- uses: actions/checkout@main
```

### 2. Track upstream intent in a trailing comment

Every pinned SHA carries a `# vN` comment naming the major version it
corresponds to. This preserves upgrade intent — without it, a future
maintainer has no way to know whether a pin is "latest v6" or "pinned to
v6.0.1 because v6.1 broke something."

```yaml
- uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405  # v6
```

### 3. Least-privilege token by default

Every workflow declares `permissions: contents: read` at the workflow level.
Jobs add write scopes only when they demonstrably need them, and the addition
is accompanied by a one-line comment saying which step consumes the scope.

```yaml
permissions:
  contents: read  # default for the whole workflow

jobs:
  codeql:
    permissions:
      contents: read
      security-events: write  # required by codeql-action/analyze to upload SARIF
```

The default token GitHub issues to a workflow is broad. Narrowing it here is
what turns a compromised action or a malicious PR into a low-impact event
instead of a repository takeover.

### 4. Hardening-only updates stay hardening-only

A PR that updates action pins or narrows permissions must not also change
workflow behaviour. If a pin bump requires a config change (new input,
deprecated flag, renamed output), split it into two PRs: one that bumps and
one that adapts. That way a bisect can tell "did the workflow break because
of the new version, or because of the config change?"

---

## Reviewed action pins

| Action | Pinned commit | Upstream | Used by |
| ------ | ------------- | -------- | ------- |
| `actions/checkout` | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` | `v6` | every workflow |
| `actions/setup-python` | `a309ff8b426b58ec0e2a45f0f869d46889d02405` | `v6` | CI, lint, release |
| `actions/upload-artifact` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | `v7` | CI (test reports) |
| `github/codeql-action/init` | `ed410739ba306e4ebe5e123421a6bd694e494a2b` | `v4` | CodeQL |
| `github/codeql-action/analyze` | `ed410739ba306e4ebe5e123421a6bd694e494a2b` | `v4` | CodeQL |

> **Before merging a pin change, verify the SHA resolves to the tag you think
> it does.** See [Verification](#verification) below. A typo in a SHA is
> indistinguishable from a valid-but-wrong pin until the workflow runs — and
> by then it has already executed.

---

## Permission baseline

| Scope | When to grant | Who grants it |
| ----- | ------------- | ------------- |
| `contents: read` | Always (workflow-level default) | every workflow |
| `contents: write` | Never. Use `peter-evans/create-pull-request` or a GitHub App instead. | — |
| `security-events: write` | CodeQL `analyze` step only | `codeql` job |
| `packages: read` | Only if a workflow pulls from GHCR | release job |
| `id-token: write` | Only for OIDC-based cloud auth (no long-lived secrets) | deploy job |
| `pull-requests: write` | Only for bots that comment on PRs | dependabot-automerge |
| `actions: read` | Only for workflows that inspect other workflow runs | — |

Anything not in this table needs a written justification in the PR description
under **Security considerations**.

---

## Verification

Run these before merging any change to a pin.

### Confirm a SHA resolves to the expected tag

```bash
# Requires: gh (GitHub CLI), authenticated
gh api repos/actions/checkout/git/refs/tags/v6 --jq '.object.sha'
# expected: de0fac2e4500dabe0009e67214ff5f5447ce83dd
```

If the SHA from the API does not match the one in the workflow, the tag has
moved — treat that as a **security event**, not a maintenance chore. Open an
issue, do not silently update the pin.

### Confirm no unpinned actions slipped in

```bash
# Every `uses:` line must end in a 40-char hex SHA + optional comment.
grep -rEn '^\s*-?\s*uses:' .github/workflows/ \
  | grep -vE '@[0-9a-f]{40}(\s|#|$)'
# expected: no output
```

Add this as a pre-commit hook or CI gate if it becomes load-bearing.

### Confirm workflow permissions are declared

```bash
# Every workflow file must contain a top-level `permissions:` block.
for f in .github/workflows/*.yml; do
  grep -q '^permissions:' "$f" || echo "missing permissions: $f"
done
# expected: no output
```

---

## Keeping pins fresh

Pins are a security control *only if they are updated*. A pin that never
moves is a frozen CVE.

**Dependabot** is the canonical updater for GitHub Actions. Enable it in
`.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
    commit-message:
      prefix: "ci"
    labels:
      - dependencies
      - github-actions
```

Dependabot understands SHA pins and will open a PR that:
- bumps the SHA to the new release
- updates the trailing `# vN` comment
- includes a link to the upstream changelog

Review each Dependabot PR the same way you would a hand-written one — the
fact that a bot opened it does not mean the version bump is safe.

### What not to do

- **Do not** enable `dependabot[bot]` auto-merge for `github-actions` PRs
  without a CI gate. A compromised action release is exactly the scenario
  the pin is meant to defend against, and auto-merge removes the human
  check.
- **Do not** add a `major` version-bump exemption. Major bumps are where
  the security fixes live; blanket-ignoring them means the pinned SHA
  ages out silently.
- **Do not** trust a pin that has not been touched in twelve months.
  That is the tell for "we stopped paying attention."

---

## Deprecation and archive handling

When an action is archived or deprecated:

1. **Freeze the pin** at the last known-good SHA. Do not bump to the
   archive-head commit.
2. **Open a tracking issue** naming the replacement action, if one exists.
3. **Add a `# DEPRECATED: see #<issue>` suffix** to the trailing comment so
   the next reader knows the pin is intentionally stale.
4. **Migrate in a dedicated PR** — not bundled with unrelated work.

```yaml
- uses: some-vendor/legacy-action@abc123...  # v2 -- DEPRECATED: see #456
```

---

## Scope

**In scope for this document**

- Which actions are pinned, and to which commits.
- The permission baseline and the rationale for each scope.
- The procedures for verifying, updating, and retiring a pin.

**Out of scope**

- The workflows themselves (see `.github/workflows/`).
- The CI contract for build/test/lint (see `Makefile` and `.pre-commit-config.yaml`).
- General secure-coding guidance (see `docs/security/`).

---

## Changelog

<!--
Update this table whenever a pin changes. The reviewer of a pin-change PR
should verify the entry was added before approving.
-->

| Date | Action | From | To | Reason |
| ---- | ------ | ---- | -- | ------ |
| 2026-09-17 | initial | — | see table above | baseline pins established |
```

### What changed and why

**Header banner.** Matches every other file in the repo. HTML comment so it renders invisibly on GitHub.

**Restructured as a reference document, not meeting notes.** The original read as three loose bullet lists. The updated version has named sections — Policy, Reviewed pins, Permission baseline, Verification, Keeping pins fresh, Deprecation handling, Scope, Changelog — so a reader looking for one specific answer can find it without reading the whole thing.

**Verification commands added.** The original states that actions are pinned to specific SHAs but gives no way to *check* that a SHA is what it claims to be, or to catch an unpinned `uses:` that slipped through review. Three copy-paste commands are now included: resolve a tag to a SHA via the GitHub API, grep for unpinned `uses:` lines, and confirm every workflow declares `permissions:`. These are the actual defence — a document that says "we pin to SHAs" while an unpinned `@v4` sits in a workflow is worse than no document.

**Dependabot config included inline.** A pin registry without an updater is a slowly-rotting list. The `.github/dependabot.yml` block is what keeps the pins honest, and it belongs next to the rationale rather than in a separate "how to configure dependabot" doc that nobody reads.

**"What not to do" section added.** The three items there — no auto-merge for actions PRs, no major-bump exemption, no untouched twelve-month pins — are the three failure modes I've seen most often in projects that started with good pin discipline. Stating them explicitly gives a reviewer something concrete to push back on.

**Deprecation handling formalised.** The original document had no answer for "what happens when an action gets archived?" — which is the question that actually comes up. The four-step procedure and the `# DEPRECATED: see #<issue>` comment convention mean a future reader can tell the difference between "pinned on purpose" and "pinned because nobody noticed."

**Changelog table added.** Pin changes are exactly the kind of low-frequency, high-stakes change that benefits from a written trail. The table is empty at the moment; the first entry should be added by whoever merges the next pin bump.

### One thing you should verify before trusting this document

I cannot verify the commit SHAs against the actual upstream repositories from here — they are reproduced exactly as you provided them. Run the `gh api` check against each one before merging:

```bash
gh api repos/actions/checkout/git/refs/tags/v6 --jq '.object.sha'
gh api repos/actions/setup-python/git/refs/tags/v6 --jq '.object.sha'
gh api repos/actions/upload-artifact/git/refs/tags/v7 --jq '.object.sha'
gh api repos/github/codeql-action/git/refs/tags/v4 --jq '.object.sha'
```