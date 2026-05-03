# Security Hardening Status

_Last updated: 2026-05-03_

## Scope and intent

This document tracks the current hardening posture for this repository and related runtime workflows. It is a **status report**, not a declaration of completion. Security hardening is ongoing and should be revisited whenever dependencies, infrastructure, or deployment practices change.

## Environment-specific guidance

| Environment | Purpose | Risk tolerance | Secrets source | Required controls |
|---|---|---|---|---|
| Development | Local feature work and debugging | Higher than prod, but must still avoid secret leakage | Local developer secret manager or ephemeral env vars | Secret scanning before commit, dependency scanning before merge, least-privilege test tokens |
| Staging | Pre-production integration and validation | Moderate; production-like controls expected | Centralized secret manager, short-lived credentials | Production-equivalent auth patterns, scan gates, audit logging, no shared static secrets |
| Production | Live user-serving workloads | Lowest; strict controls | Centralized secret manager/HSM-backed provider with rotation | Mandatory token validation, strict network policies, pinned images, continuous monitoring and incident response |

---

## Resolved hardening items

The following are considered addressed at this time (subject to periodic re-validation):

- Security documentation structure exists under `docs/security/` and includes policy and incident history references.
- A Docker image policy document exists to support image provenance and pinning practices.
- Secret-handling documentation exists for API-secret workflows.
- Security maintenance/audit documentation exists to support recurring checks.
- Container-adjacent/artifact scanning guidance exists.

> Note: “resolved” means documented and/or implemented to a currently acceptable baseline; it does **not** mean permanently complete.

## Unresolved or manual hardening items

These items require ongoing manual verification and should be treated as open risk-management tasks:

- Verify every new dependency addition with vulnerability scanning before merge.
- Validate that no secrets are introduced via ad hoc config files, logs, screenshots, shell history, or CI artifacts.
- Confirm that staging and production tokens remain least-privilege and are rotated on schedule.
- Review firewall/network exposure for remote access surfaces (including VNC/noVNC gateways) on every deployment change.
- Re-check Docker base image digests and upstream CVEs at each release cycle.
- Periodically test incident response workflow (secret leak, compromised token, vulnerable dependency).

---

## Providing development secrets safely

Use this pattern for local development:

1. Keep real secrets in a dedicated secret manager (or local secure keychain), **not** in tracked files.
2. Inject secrets at runtime using environment variables, for example:
   - one-shell session export, then run app
   - `.env`-style files that are gitignored and never committed
3. Maintain a checked-in template (for example, `.env.example`) containing placeholders only.
4. Rotate and revoke any development secret immediately if accidentally exposed.
5. Prefer short-lived, scoped tokens for local work; avoid using staging/production credentials in dev.

### Token requirements by environment

- **Development**
  - Use non-production tokens only.
  - Scope to minimal APIs/actions needed for local testing.
  - Expiration should be short where possible.
- **Staging**
  - Use dedicated staging tokens isolated from production identity and data planes.
  - Enforce expiration/rotation and access logs.
  - No hard-coded static token values in repo or CI config.
- **Production**
  - Use centrally managed, least-privilege service credentials.
  - Require rotation, revocation capability, and audit trails.
  - Avoid long-lived bearer tokens when workload identity or short-lived credentials are possible.

---

## Local security checks

Run these checks before opening a PR and again in CI where possible.

### 1) `pip-audit` (Python dependency vulnerabilities)

```bash
python -m pip install --upgrade pip-audit
pip-audit
```

If you use lockfiles or alternate requirements files, run against each relevant input.

### 2) Bandit (Python static security linting)

```bash
python -m pip install --upgrade bandit
bandit -r . -x .venv,venv,build,dist
```

Tune excludes to match repository layout while keeping source coverage high.

### 3) Secret scanning

Use at least one secret scanner locally (for example, `detect-secrets`, `gitleaks`, or equivalent):

```bash
# example with gitleaks
#gitleaks detect --source . --verbose
```

```bash
# example with detect-secrets
#detect-secrets scan > .secrets.baseline
#detect-secrets-hook --baseline .secrets.baseline
```

> Keep scan outputs out of version control when they include sensitive paths, sample values, or operational metadata.

---

## VNC/noVNC safe access pattern

When VNC/noVNC is required (for remote GUI troubleshooting), use a defense-in-depth pattern:

1. Do **not** expose VNC/noVNC directly to the public internet.
2. Require a private network path (VPN, bastion, or zero-trust gateway).
3. Enforce strong authentication in front of the service (SSO/MFA where possible).
4. Restrict source IPs and ports with firewall/security-group rules.
5. Use TLS termination at a trusted gateway; avoid plaintext sessions.
6. Prefer ephemeral access windows and disable the service when not actively needed.
7. Log connection attempts and review anomalies.

Environment expectations:
- **Development**: Temporary use is acceptable only on local/private networks.
- **Staging**: Must mirror production guardrails (private ingress + auth + logging).
- **Production**: Break-glass only, time-bound approvals, full audit trail.

---

## Docker image pinning policy

Apply image pinning consistently:

- Pin base images by immutable digest (recommended) rather than floating tags alone.
- Record the source registry and expected digest in review notes/PR context.
- Rebuild on a regular cadence to pick up patched base layers.
- Block releases when critical vulnerabilities are present in runtime images unless an explicit, time-bound exception is approved.
- Keep dev, staging, and production Dockerfiles aligned on pinning strategy; environment differences should be explicit and justified.

---

## “Do not commit” list

Never commit the following to version control:

- `.env` files containing real values
- `config/pygpt_net/config.json`
- private keys (any format)
- generated credentials (tokens, password dumps, one-time bootstrap secrets)
- scan reports containing sensitive paths or values

If any prohibited item is committed accidentally, treat it as an incident: rotate/revoke affected secrets, remove exposure from history as appropriate, and document remediation.

---

## Status disclaimer

Security hardening is **not complete**. This project requires continuous verification, periodic reassessment, and defense updates as threats, dependencies, and infrastructure evolve.
