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
| P1 | Power and uninstall paths previously ran privileged commands without central confirmation. PR #860 added a local intent gate, deny-by-default, an API confirmation header and uninstaller path checks. This branch adds distinct operator/admin API token roles for power shutdown; other GUI/agent/container mutations still require separate inventory and gating. | Maintainer / runtime | **Partial:** direct host-action gate and scoped API token roles implemented; the global token maps to operator, and power shutdown requires admin scope plus explicit confirmation. The library `actor_role` remains a caller claim outside authenticated API ingress; per-user identity/audit and connector/agent capability inventory remain open. | [PR #860](https://github.com/DylanLRPollock/Monkey-Head-Project/pull/860), [issue #852](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/852) |
| P1 | Coverage gate remains **80%**. After setting the pytest-asyncio fixture loop scope, CI run [#42457244887](https://github.com/DylanLRPollock/Monkey-Head-Project/actions/runs/42457244887) collected 546 passing and 16 skipped tests; combined coverage is **36.34%**. The function-body tracing probe passes on Python 3.13. | Maintainer / quality | **Open:** instrumentation and collection now work, but coverage remains far below 80%. Add deterministic success/error/rollback tests across maintained runtime modules; do not exclude them or lower the threshold. | [issue #847](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/847) |
| P2 | The original Ruff backlog was 595 diagnostics. This branch's CI diagnostic report records **0 remaining Ruff diagnostics** after fixing the three diagnostics found on the current main revision. The first full lint run passed dependency-sync/canon checks but stopped at one Black formatting difference; that final formatting fix is on the branch and awaits a fresh full lint result. | Maintainer / quality | **In progress:** the Ruff count is zero; keep the issue open until the full static-analysis job passes, including Black, isort, Ruff and flake8. | [issue #848](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/848) |
| P2 | Historical alternates remain beside canonical `.editorconfig`, `.flake8`, `.pre-commit-config.yaml`, and `pyproject.toml`; `pytest.ini` has already been removed. | Maintainer / tooling | **Partial:** automatic entrypoints and exceptions are documented; alternates remain inert but tracked pending external tooling/reference audit. | [issue #854](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/854) |
| P2 | Binary, vendor and generated artifacts have substantial review, licensing and provenance costs. | Maintainer / release | **Open release process:** classify retention, produce checksums and SBOM for distributables, retain license notices and reproducible source references. Never delete for a green check. | [issue #854](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/854) |

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
