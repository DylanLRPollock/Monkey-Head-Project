# Current security and quality risk register — 2026-11-03

**Scope:** Monkey-Head-Project default branch and supported Python 3.13
runtime. This is a point-in-time evidence register, not an assurance of
production readiness. **Owner:** repository maintainer unless assigned
otherwise in a linked issue. Update after changes to control surfaces, CI,
dependency manifests or hardware exposure.

| Priority | Risk / evidence | Owner | Gate and current disposition | Tracking |
| --- | --- | --- | --- | --- |
| P0 | A credential-shaped secret was previously committed. PR #850 removed the live-document copy, **not** historic objects, forks or released artifacts. Revocation and usage review have not been independently confirmed. | Maintainer / credential owner | **Open operational gate:** verify rotation/revocation, audit usage, then plan coordinated history and artifact handling. Do not publish the literal value. | [PR #850](../../pull/850), [incident runbook](openai-api-key-incident.md) |
| P1 | Bearer auth and Host-header trust bug: PR #851 enforces configured token on non-health endpoints and uses peer identity, not request Host. Fine-grained roles and trusted-proxy policy are still absent. | Maintainer / API | **Partial:** merged code; CI and deployment checks required; RBAC is not implemented. | [PR #851](../../pull/851), [issue #852](../../issues/852) |
| P1 | Power and uninstall paths previously ran privileged commands without central confirmation. PR #860 added a local intent gate, deny-by-default, an API confirmation header and uninstaller path checks. GUI/agent/container mutations are not yet uniformly covered. | Maintainer / runtime | **Partial:** direct host-action gate implemented. No authenticated user identity is inferred from a function argument or a header. Finish connector/agent capability gating and platform tests. | [PR #860](../../pull/860), [issue #852](../../issues/852) |
| P1 | Coverage CI's **80%** gate is failing: historical job showed 36% combined coverage, XML reported 42.33% line and 3.70% branch coverage. Source aliases/tracing need validation. | Maintainer / quality | **Open:** retain `fail_under = 80`; verify body-line tracing and expand deterministic success/error/rollback tests without hiding maintained modules. | [issue #847](../../issues/847) |
| P2 | Ruff reported 595 diagnostics in the November 2026 Python 3.13 job. Most were modern-typing issues, but E402 and Enum fixes need compatibility review. | Maintainer / quality | **Open:** Black/isort pass in referenced CI; Ruff failing. Modernize by domain. No blanket rule exclusions. | [issue #848](../../issues/848) |
| P2 | `.editorconfig` / `editorconfig`, `.flake8` / `flake8.ini`, `.pre-commit-config.yaml` / `pre-commit.yaml`, plus `pytest.ini` overriding pyproject pytest config. | Maintainer / tooling | **Open:** canonical configuration mapping documented. Remove alternates only after reference audit; consolidate pytest settings into pyproject. | [issue #854](../../issues/854) |
| P2 | Binary, vendor and generated artifacts have substantial review, licensing and provenance costs. | Maintainer / release | **Open release process:** classify retention, produce checksums and SBOM for distributables, retain license notices and reproducible source references. Never delete for a green check. | [issue #854](../../issues/854) |

## Controls verified in the default-branch tree

- `.github/workflows/security-dependency-scan.yml` runs `pip-audit` with
  enforced failure on unaccepted advisories on PRs, main pushes and a weekly
  schedule. It audits the installed pinned dev environment. This does **not**
  imply every optional dependency or a deployed environment has been audited.
- The 17-workflow November inventory in [issue #854](../../issues/854) reports
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

[Security concerns and fixes (April 29)](security-concerns-and-fixes.md),
[threat model v101.1 (May 12)](threat-model-v101.1.md) and
[security hardening status (May 3)](security-hardening-status.md) are
**historical snapshots**. When their proposed future work conflicts with
this register, verify the implementation/CI on the current branch instead of
silently treating an older plan as a current defect.
