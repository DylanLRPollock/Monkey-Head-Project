# Current security and quality risk register — reviewed 2026-11-09

**Scope:** Monkey-Head-Project default branch and supported Python 3.13
runtime. This is a point-in-time evidence register, not an assurance of
production readiness. **Owner:** repository maintainer unless assigned
otherwise in a linked issue. Update after changes to control surfaces, CI,
dependency manifests or hardware exposure.

| Priority | Risk / evidence | Owner | Gate and current disposition | Tracking |
| --- | --- | --- | --- | --- |
| P0 | A credential-shaped secret was previously committed. PR #850 removed the live-document copy, **not** historic objects, forks or released artifacts. Revocation and usage review have not been independently confirmed. | Maintainer / credential owner | **Open operational gate:** verify rotation/revocation, audit usage, then plan coordinated history and artifact handling. Do not publish the literal value. | [PR #850](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/850), [incident runbook](https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/security/openai-api-key-incident.md) |
| P1 | Bearer auth and Host-header trust bug: PR #851 enforces configured token on non-health endpoints and uses peer identity, not request Host. Fine-grained roles and trusted-proxy policy are still absent. | Maintainer / API | **Partial:** merged code; CI and deployment checks required; RBAC is not implemented. | [PR #851](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/851), [issue #852](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/852) |
| P1 | Power, uninstall, install/update, account, command, failover, repair, Docker and Kubernetes entrypoints require scoped local intent; merged PR #870 extends direct-call guards and caller coverage. Local role values and process opt-ins do not identify a human principal. Shared API tokens have no per-user identity, and plugin/agent capability inventory remains incomplete. | Maintainer / runtime | **Partial:** local direct-call gates are merged. Named-principal RBAC, task ownership, a complete third-party capability registry and action audit records remain open. | [PR #870](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/870), [privilege and identity audit](privilege-and-identity-audit-2026-11-08.md), [issue #852](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/852) |
| P1 | Coverage gate remains **80%**. The merged baseline had 36.34% combined coverage with runtime source exclusions. PRs #869 and #871 removed the source omissions and added fixture-registry, proof-loop, API privilege, wiki, root-entrypoint, infrastructure preflight, FFmpeg-manager, and public media-operation tests. Python 3.13 and 3.14 CI report **606 passed, 16 skipped, and 26.75% combined coverage**; the tracing probe reaches a function body in `memory/indexing.py`. | Maintainer / quality | **Open:** scope is the full `src/huey` tree and the threshold remains 80%; coverage is more honest but remains far below target. PR #872 adds isolated regressions for atomic storage-write recovery and storage-root path confinement. | [PR #872](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/872), [issue #847](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/847) |
| P2 | The original Ruff backlog was 595 diagnostics. PR #867 cleared the Ruff backlog; this follow-up removes the prior maintained-code flake8 findings and expands the configured flake8 scan to root entrypoints and `infra/`. Vendored code and documented legacy compatibility trees remain excluded. | Maintainer / quality | **Locally verified:** repository-wide flake8 under `.flake8` reports zero findings; CI Black/isort/Ruff scope remains unchanged. | [issue #848](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/848) |
| P2 | CodeQL's PR #870 check reported a side-effecting `assert` in `tests/test_failover.py`; this is a test reliability finding, not a reported production command-injection alert. | Maintainer / quality | **Fix included, scan pending:** PR #872 moves execution calls out of assertions and verifies their results separately. | [PR #870](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/870), [PR #872](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/872) |
| P2 | Historical alternates remain beside canonical .editorconfig, .flake8, .pre-commit-config.yaml, and pyproject.toml; pytest.ini has already been removed. | Maintainer / tooling | **Repository reference audit complete in merged PR #871:** no active in-repository selectors found; check maintainer-local tooling before removal. | [configuration reference audit](../development/config-reference-audit-2026-11-08.md), [issue #854](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/854) |
| P2 | Binary, vendor and generated artifacts have substantial review, licensing and provenance costs. | Maintainer / release | **Partial:** artifact hashing, runtime SBOM and checksum verification are implemented. Four existing GitHub prereleases have no assets; ten tracked files exceed 5 MiB and still need owner/origin/license/consumer review. GitHub asset attestations are absent for future releases. | [release artifact audit](../release/artifact-audit-2026-11-08.md), [issue #854](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/854) |

## Controls verified in the default-branch tree

- `.github/workflows/security-dependency-scan.yml` runs `pip-audit` with
  enforced failure on unaccepted advisories on PRs, main pushes and a weekly
  schedule. It audits the installed pinned dev environment. This does **not**
  imply every optional dependency or a deployed environment has been audited.
- The 17-workflow November inventory in [issue #854](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/854) reports
  52 full 40-character SHA-pinned action references. Recheck before claiming
  this for a future commit.
- `scripts/security/security_check.sh` deliberately warns/skips when the
  local `pip-audit` binary is absent. Local checks are therefore **not**
  equivalent to mandatory CI security gates.
- PRs #850, #851, #870 and #871 were merged by November 9, 2026. A merge is not
  evidence that historic credentials were revoked or that role isolation is
  complete.

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
