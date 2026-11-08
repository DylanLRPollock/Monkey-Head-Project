# Current security and quality risk register — 2026-11-08

**Scope:** Monkey-Head-Project default branch and supported Python 3.13
runtime. This is a point-in-time evidence register, not an assurance of
production readiness. **Owner:** repository maintainer unless assigned
otherwise in a linked issue. Update after changes to control surfaces, CI,
dependency manifests or hardware exposure.

| Priority | Risk / evidence | Owner | Gate and current disposition | Tracking |
| --- | --- | --- | --- | --- |
| P0 | A credential-shaped secret was previously committed. PR #850 removed the live-document copy, **not** historic objects, forks or released artifacts. Revocation and usage review have not been independently confirmed. | Maintainer / credential owner | **Open operational gate:** verify rotation/revocation, audit usage, then plan coordinated history and artifact handling. Do not publish the literal value. | [PR #850](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/850), [incident runbook](https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/security/openai-api-key-incident.md) |
| P1 | Bearer auth and Host-header trust bug: PR #851 enforces configured token on non-health endpoints and uses peer identity, not request Host. Fine-grained roles and trusted-proxy policy are still absent. | Maintainer / API | **Partial:** merged code; CI and deployment checks required; RBAC is not implemented. | [PR #851](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/851), [issue #852](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/852) |
| P1 | Power and uninstall paths previously ran privileged commands without central confirmation. PR #860 added a local intent gate, deny-by-default, an API confirmation header and uninstaller path checks. The current API distinguishes operator/admin only for shutdown and now blocks unauthenticated non-loopback access when no tokens are configured. Shared tokens still have no per-user identity; other mutating API routes share global bearer access, while plugin/agent capability inventory remains incomplete. | Maintainer / runtime | **Audited; follow-up remains:** see [privilege and identity audit](privilege-and-identity-audit-2026-11-08.md). Do not treat body-provided actor or approval names as verified identities. | [PR #860](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/860), [issue #852](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/852) |
| P1 | Coverage gate remains **80%**. The merged baseline had 36.34% combined coverage with runtime source exclusions. This branch removes all coverage source omissions and adds targeted fixture-registry, proof-loop, API privilege, wiki, root-entrypoint, and infrastructure preflight tests. Current local Python 3.13 run: **31.81% line coverage, 2.86% branch coverage, 27% combined**, with 586 passing and 13 skipped. | Maintainer / quality | **Open:** scope is the full `src/huey` tree and the threshold remains 80%; coverage is more honest but still far below target. Add deterministic success/error/rollback tests across the large untested legacy and runtime surfaces. | [issue #847](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/847) |
| P2 | The original Ruff backlog was 595 diagnostics. PR #867 cleared the Ruff backlog; this follow-up removes the prior maintained-code flake8 findings and expands the configured flake8 scan to root entrypoints and `infra/`. Vendored code and documented legacy compatibility trees remain excluded. | Maintainer / quality | **Locally verified:** repository-wide flake8 under `.flake8` reports zero findings; CI Black/isort/Ruff scope remains unchanged. | [issue #848](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/848) |
| P2 | Historical alternates remain beside canonical .editorconfig, .flake8, .pre-commit-config.yaml, and pyproject.toml; pytest.ini has already been removed. | Maintainer / tooling | **Repository reference audit complete:** no active in-repository -c / --config consumers found. Alternates retained as historical pending separate maintainer-local automation check. | [configuration reference audit](../development/config-reference-audit-2026-11-08.md), [issue #854](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/854) |
| P2 | Binary, vendor and generated artifacts have substantial review, licensing and provenance costs. | Maintainer / release | **Audit complete; automation added:** complete commit-tied file hashes and CycloneDX runtime SBOM are emitted; release checksum manifest is verified before publish. Individual legacy payload origin/license and GitHub asset signatures remain review items. | [release artifact audit](../release/artifact-audit-2026-11-08.md), [issue #854](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/854) |

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
- PR #850 and PR #851 were merged on November 3, 2026. A merge is not
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
