# Current security and quality risk register — reviewed 2026-11-09

**Scope:** Monkey-Head-Project default branch and supported Python 3.13
runtime. This is a point-in-time evidence register, not an assurance of
production readiness. **Owner:** repository maintainer unless assigned
otherwise in a linked issue. Update after changes to control surfaces, CI,
dependency manifests or hardware exposure.

| Priority | Risk / evidence | Owner | Gate and current disposition | Tracking |
| --- | --- | --- | --- | --- |
| P0 | A credential-shaped secret was previously committed. PR #850 removed the live-document copy, **not** historic objects, forks or released artifacts. Revocation and usage review have not been independently confirmed. | Maintainer / credential owner | **Open operational gate:** verify rotation/revocation, audit usage, then plan coordinated history and artifact handling. Do not publish the literal value. | [PR #850](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/850), [incident runbook](https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/security/openai-api-key-incident.md) |
| P1 | Bearer auth and Host-header trust bug: PR #851 enforces configured credentials on non-health endpoints and uses peer identity, not request Host. Named operator/admin roles and task owner checks now exist for named API principals. | Maintainer / API | **Partial:** external identity-provider integration, trusted-proxy deployment policy, shared-token aggregation, and third-party capability coverage remain open. | [PR #851](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/851), [PR #887](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/887), [PR #890](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/890), [issue #852](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/852) |
| P1 | Power, uninstall, install/update, account, command, failover, repair, Docker and Kubernetes operations are guarded by a shared local capability gate. Named API credentials, owner-scoped task routes, HTTP mutation logs, and direct in-process gate-decision logs are merged. | Maintainer / runtime | **Partial:** role values remain local claims, shared tokens aggregate callers, and application logs are not tamper-resistant. A complete third-party plugin/agent capability registry and external identity integration remain open. | [PR #870](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/870), [PR #887](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/887), [PR #888](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/888), [PR #890](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/890), [privilege and identity audit](privilege-and-identity-audit-2026-11-08.md), [issue #852](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/852) |
| P1 | The combined coverage gate remains **80%** with the full `src/huey` tree measured; no maintained source is omitted. Latest full CI (PR #896): Python 3.13 and 3.14 each report **750 passed, 16 skipped**, with **56.45%** combined coverage. Coverage tracing validation and static analysis pass; the only CI failure is the unchanged 80% threshold. `huey.runtime.orchestrator` now has **100% line and branch coverage**. Other focused modules remain: honeycomb storage 81%, memory indexing 96%, V1 fixture registry 97%, system checks 81%, power management 83%, platform support 94%, and media manager 94%. | Maintainer / quality | **Open:** broad full-source coverage remains far below target; continue fixture-based success/error/rollback tests and track module-level line/branch reports. Do not satisfy the gate by removing maintained modules from scope. | [PR #872](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/872), [PR #873](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/873), [PR #874](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/874), [PR #875](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/875), [PR #876](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/876), [PR #877](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/877), [PR #891](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/891), [PR #896](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/896), [issue #847](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/847) |
| P2 | The original Ruff backlog was 595 diagnostics. PR #867 cleared the Ruff backlog; this follow-up removes the prior maintained-code flake8 findings and expands the configured flake8 scan to root entrypoints and `infra/`. Vendored code and documented legacy compatibility trees remain excluded. | Maintainer / quality | **Locally verified:** repository-wide flake8 under `.flake8` reports zero findings; CI Black/isort/Ruff scope remains unchanged. | [issue #848](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/848) |
| P2 | CodeQL's PR #870 check reported a side-effecting `assert` in `tests/test_failover.py`; this is a test reliability finding, not a reported production command-injection alert. | Maintainer / quality | **Fixed and verified:** PR #872 moves execution calls out of assertions; its CodeQL Advanced workflow passed. | [PR #870](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/870), [PR #872](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/872) |
| P2 | Historical alternates remain beside canonical .editorconfig, .flake8, .pre-commit-config.yaml, and pyproject.toml; pytest.ini has already been removed. | Maintainer / tooling | **Repository reference audit complete in merged PR #871:** no active in-repository selectors found; check maintainer-local tooling before removal. | [configuration reference audit](../development/config-reference-audit-2026-11-08.md), [issue #854](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/854) |
| P2 | Binary, vendor and generated artifacts have substantial review, licensing and provenance costs. | Maintainer / release | **Partial:** artifact hashing, runtime SBOM, checksums, and GitHub attestation generation for future package releases are configured. Four existing GitHub prereleases have no assets; ten tracked files over 5 MiB still need owner/origin/license/consumer review. A tagged package release is required to verify actual GitHub attestations. | [PR #889](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/889), [release artifact audit](../release/artifact-audit-2026-11-08.md), [issue #854](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/854) |

## Controls verified in the default-branch tree

- `.github/workflows/security-dependency-scan.yml` runs `pip-audit` with
  enforced failure on unaccepted advisories on PRs, main pushes and a weekly
  schedule. It audits the installed pinned dev environment. This does **not**
  imply every optional dependency or a deployed environment has been audited.
- The 17-workflow November inventory in [issue #854](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/854) reported
  52 full 40-character SHA-pinned action references. Merged PR #889 added one
  more full-SHA-pinned action; recheck the total after future workflow changes.
- `scripts/security/security_check.sh` deliberately warns/skips when the
  local `pip-audit` binary is absent. Local checks are therefore **not**
  equivalent to mandatory CI security gates.
- PRs #850, #851, #870-#871, #883, #887-#897 were merged by November 9, 2026.
  A merge is not evidence that historic credentials were revoked, external
  identity is verified, or artifact attestations have been exercised on a
  tagged release.

## Release and artifact retention decision log

Before moving a generated archive, binary or vendor tree, record the owning
component, license/NOTICE requirements, origin commit or version, intended
consumer, build recipe, checksum (SHA-256), SBOM provenance, GitHub Release or
content-addressed storage location and rollback/retrieval instructions.
Preserve any reproducibility evidence and do not rehost upstream proprietary
payloads without licensing review. This policy is **required work**, not a
claim that the current repository contains all these records.

## Test taxonomy and escape conditions

See [test-suite taxonomy](../testing/test-suite-taxonomy.md). Unit tests must
have deterministic fixtures and no host/network/process side effects; integration
tests may invoke temporary test services; platform/hardware tests must identify
host requirements and meaningful skips; end-to-end tests must record target
environment and operator safety gates. A passing test count is not a replacement
for the required coverage and security gates.

## Historical context

[Security concerns and fixes (April 29)](https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/security/security-concerns-and-fixes.md),
[threat model v101.1 (May 12)](https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/security/threat-model-v101.1.md) and
[security hardening status (May 3)](security-hardening-status.md) are
**historical snapshots**. When their proposed future work conflicts with
this register, verify the implementation/CI on the current branch instead of
silently treating an older plan as a current defect.
