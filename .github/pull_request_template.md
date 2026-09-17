<!--
# ---------------------------------------------------------------------------
# Monkey-Head-Project
# Component: Repository / Pull Request Template
# Author: Dylan L.R. Pollock
# Documentation: https://www.dlrp.ca
#
# Philosophy: Breathing new life into old tech.
# ---------------------------------------------------------------------------

Fill in every section. Delete sections that genuinely do not apply
(e.g. "Screenshots/logs" for a pure backend change) -- but do not delete
the section merely because it is inconvenient. Reviewers scan this file
top-to-bottom; an empty section is a signal something was skipped.

Keep the `##` headings. They are used by tooling that summarises PRs.
-->

## Summary

<!--
One or two sentences a reviewer can read before opening the diff.
If you cannot summarise the change without a paragraph, the PR is
probably too large. Split it.
-->

-

## Why

<!--
The problem this solves. Link the issue if one exists:
`Closes #123` / `Fixes #123` / `Relates to #123`.

If there is no issue, explain what broke, what was missing, or what
prompted the change. "Cleanup" and "refactor" alone are not reasons --
say *what* the cleanup enables or what the refactor unblocks.
-->

-

## Type of change

<!-- Tick exactly one primary type. Secondary types can be noted after. -->

- [ ] Bug fix (non-breaking change that resolves an issue)
- [ ] Feature (non-breaking change that adds capability)
- [ ] Refactor (no behaviour change)
- [ ] Performance improvement
- [ ] Documentation only
- [ ] Build / CI / tooling
- [ ] Security fix or hardening
- [ ] Breaking change (see **Breaking changes** below)
- [ ] Revert (reference the PR being reverted)

## Scope

**In scope**

-

**Out of scope**

<!--
Name the adjacent work you deliberately did not do. This is the single
most useful section for a reviewer trying to decide whether a concern
is a blocker or a follow-up.
-->

-

## Tests run

<!--
List the commands you actually ran, not the ones you meant to run.
Copy-paste from the terminal is fine -- a reviewer should be able to
reproduce your verification exactly.

The `make` targets below are the expected minimum for a code change.
Delete rows that do not apply, and add rows for anything else you ran
(e.g. a specific `pytest -k ...`, a manual `curl`, a browser check).
-->

- [ ] `make lint` (guardrails + black/isort/ruff/flake8)
- [ ] `make test` (pytest)
- [ ] `make coverage` (if touching logic with meaningful branches)
- [ ] `make check-deps-sync` (if dependency files changed)
- [ ] `pre-commit run --all-files`

Additional commands and results:

```
# paste the exact commands and their output here
```

## Screenshots / logs (if UI or observable behaviour changes)

<!--
Attach screenshots for any UI-visible change. Attach log excerpts for
any change to startup, shutdown, error paths, or the API surface.
Redact tokens, keys, and any personally identifying information.

If not applicable, write "N/A" here -- do not leave this blank.
-->

N/A

## Security considerations

<!--
Answer every prompt. "No impact" is a valid answer; leaving it blank
is not. Bandit, gitleaks, and pip-audit run on every commit, but they
only catch known patterns -- they cannot reason about your intent.

Prompts to consider:
  * Does this touch authentication, authorisation, or token handling?
  * Does this add or change a network listener, client, or protocol?
  * Does this shell out? If so, is the argv list-form (no shell=True)?
  * Does this read user-supplied paths, filenames, or URLs?
  * Does this introduce a new dependency? What is its maintenance story?
  * Does this log anything that could contain a secret or PII?
  * Does this weaken a default (e.g. CORS, TLS verification, timeouts)?
-->

-

## Docs updated

- [ ] Yes -- updated: `...`
- [ ] No -- because: `...`
- [ ] N/A (change is internal-only and not user-observable)

<!--
"Code is the docs" is not an acceptable answer for a user-visible
change. If a new setting, CLI flag, endpoint, or behaviour is added
and nothing in `docs/` or `README.md` mentions it, that is a bug in
the PR, not a follow-up.
-->

## Dependency changes

- [ ] None
- [ ] Yes -- see table below and confirm `make check-deps-sync` passes

| Package | Change | Reason |
| ------- | ------ | ------ |
|         |        |        |

<!--
Every dependency addition is a liability. State the reason in terms of
what it unblocks, not what it is. If it duplicates existing capability,
explain why the existing tool is insufficient.

If the change is a version bump only, note whether it is a security
advisory, a bug fix you needed, or routine maintenance.
-->

## Breaking changes

<!--
If this PR changes a public interface, a config key, a wire format, or
a default that downstream consumers rely on, describe:
  * What breaks
  * Who is affected
  * The migration path
  * Whether a deprecation shim is included

If none, write "None".
-->

None

## Rollback plan

<!--
How to undo this if it turns out badly in production. For a pure code
change this is usually "revert the merge commit". For anything that
touches persistent state, config, or a database, say what the rollback
actually involves.
-->

-

## Boundary check

<!--
The project has an explicit architecture. These three statements are
load-bearing and must remain true. If a change makes any of them false,
the PR needs an explicit architectural discussion -- do not merge it by
weakening the assertion.

If you are unsure what any of these mean, read `docs/architecture.md`
before ticking the box.
-->

- [ ] This keeps **PyHuey** as cockpit / tooling -- it does not promote
      PyHuey into a runtime dependency of HueyOS itself.
- [ ] This keeps **Huey Brain V1** running on the **Legion Go** -- no
      change moves inference, memory, or control off that host.
- [ ] This avoids implying **Huey Body / HIMS / live mic** are active --
      no docs, no API responses, no CLI output claim these are
      operational when they are not.

## Reviewer notes

<!--
Optional. Anything you want a reviewer to pay particular attention to:
a subtle invariant, a line you are unsure about, a trade-off you made.
This is the right place to say "I chose X over Y because ...".
-->

-

---

<sub>
Before requesting review, confirm the PR title follows the convention
`<component>: <short imperative summary>`, e.g.
`hueyos/api: add /healthz readiness probe`.
</sub>
```