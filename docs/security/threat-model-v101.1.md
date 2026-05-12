# Threat Model (v101.1)

_Last updated: 2026-05-12_

## Scope

This threat model summarizes current v101.1 security scan and hardening notes for the Monkey-Head-Project repository, with emphasis on HueyOS runtime and PyHuey cockpit surfaces that are present today.

This is a risk-management snapshot, **not** a claim of complete security. Where controls are not fully shipped, they are marked as **Planned** or **Assumed**.

## Assets to protect

1. **Operator credentials and API secrets** (for local/bridge cognition providers and service APIs).
2. **Control-plane integrity** for admin/governance/resilience/system endpoints that can start/stop services or run automation actions.
3. **Host and container execution integrity** where helper scripts or runtime tools can execute commands or mutate files.
4. **Local data stores and generated artifacts** (context DBs, logs, structured run records, exports).
5. **Build and release integrity** (container images, dependency locks, CI artifacts, bundled binaries/archives).

## Trust boundaries

1. **Local trusted operator boundary**
   - Localhost-only admin/API usage and local CLI operations.
2. **Remote network boundary**
   - Any access crossing loopback into LAN/WAN/reverse-proxy/VPN paths.
3. **Container boundary**
   - Runtime behavior inside Docker images vs. host privileges/mounts.
4. **Repository/CI boundary**
   - Source-controlled code vs. generated artifacts and external dependencies.
5. **External provider boundary**
   - API-backed cognition/tooling services outside local sovereignty.

## Attacker-controlled inputs

1. **HTTP request data** (headers, body, path params) reaching API routes.
2. **Network reachability and probing attempts** against published container/API/VNC ports.
3. **Potentially malicious dependency or supply-chain inputs** in upstream packages or containers.
4. **Untrusted file/path/content inputs** if exposed through automation or plugin/tool execution surfaces.

## Operator-controlled inputs

1. **Environment variables** (including `HUEY_API_TOKEN`, bind addresses, runtime flags).
2. **Compose/deployment settings** (port publishing, mounted volumes, runtime profile choices).
3. **Secret manager material and token lifecycle actions** (rotation/revocation).
4. **Operational command invocations** for local management helpers and deployment scripts.

## Developer-controlled inputs

1. **Source code and routing behavior** in API, runtime, and tooling modules.
2. **Dependency declarations and pins** in `pyproject.toml`, `requirements.txt`, and container Dockerfiles.
3. **CI/workflow controls** for scanning gates and release automation.
4. **Security policy/docs/baselines** (Bandit baseline usage, scanning guidance, incident notes).

## Attack surfaces

1. **FastAPI control surface** (system/admin/governance/resilience/network/task routes).
2. **Runtime command/tool execution surfaces** in helper scripts and agent/cockpit tooling.
3. **Container exposure surfaces** (published ports, bind addresses, host mounts, VNC/noVNC access paths).
4. **Dependency and artifact ingestion surfaces** (Python packages, vendored trees, large binary archives).
5. **Secrets handling surfaces** (environment injection, config files, logs, CI artifacts).

## Mitigations (with implementation status)

| Mitigation | Status | Notes |
|---|---|---|
| Optional bearer-token gate for API with `HUEY_API_TOKEN`; `/healthz` exempt | **Implemented** | Documented as already added; remote use should set token. |
| Local-only default binding (`127.0.0.1`) for key local service paths | **Implemented** | Documented as hardening change; explicit override needed for broader exposure. |
| noVNC/VNC password requirement and localhost-only raw VNC listener in container | **Implemented** | Reduces unauthenticated GUI exposure risk, but still needs secure front-door controls when remote. |
| Shell execution hardening for `--sys-code` (no `shell=True`) | **Implemented** | Injection resistance improved for this path; still a powerful surface. |
| Structured security docs/policies and incident records in `docs/security/` | **Implemented** | Provides process control and review guidance; not a runtime enforcement control by itself. |
| CI/local dependency vulnerability scanning (`pip-audit`) as required gate | **Planned** | Called out as remaining concern / recommended control. |
| Role-based authz split for operator/admin/governance actions | **Planned** | Current token gate is coarse; finer privilege boundaries still pending. |
| Secure production deployment profile (private ingress, hardened mounts, auth-required defaults) | **Planned** | Hardening guidance exists; complete enforced profile remains in-progress. |
| Action pinning to commit SHAs in GitHub workflows | **Planned** | Identified as remaining concern. |
| Submodule/release artifact governance (pin reviewed commits, reduce heavy in-repo artifacts) | **Planned** | Identified as supply-chain/review-surface reduction work. |
| Least-privilege token issuance/rotation and safe secret storage practices | **Assumed** | Threat severity depends on operator following documented secret handling/rotation guidance. |
| Private network path + TLS + strong front-door auth for remote VNC/noVNC access | **Assumed** | Guidance exists; severity increases materially if not enforced operationally. |

## Severity calibration

This model uses pragmatic severity bands for current v101.1 operations:

- **Critical**: Unauthenticated or weakly protected paths that can trigger privileged control actions remotely.
- **High**: Control/action surfaces where a single misconfiguration (token unset + broad bind/publish) can permit meaningful system abuse.
- **Medium**: Supply-chain/documentation/process weaknesses that increase exploit likelihood over time.
- **Low**: Documentation drift or hygiene issues without immediate exploitability.

### Current calibration snapshot

1. **API control-surface misuse**: **High** currently (can move toward Medium when role-based authz + hardened deployment defaults are enforced).
2. **Secrets leakage via ops/config/logging mistakes**: **High** due to impact, though partially mitigated by documented handling and rotation playbooks.
3. **Dependency/supply-chain risk**: **Medium-High** while scanning/pinning hard gates are still being completed.
4. **VNC/noVNC exposure mistakes**: **High** if remote access controls are weak; **Medium** when private ingress + auth + TLS are consistently enforced.

## Assumptions that reduce severity

These assumptions lower practical risk **only if true in deployment**:

1. API is bound to localhost/private network by default and not directly internet-exposed.
2. `HUEY_API_TOKEN` (or stronger control) is configured for any non-local access.
3. Operators use least-privilege, short-lived credentials with regular rotation.
4. VNC/noVNC is enabled only when needed and protected by private ingress plus strong auth.
5. Security scans (Bandit baseline discipline + dependency audits + secret checks) run before merge/release.

## Assumptions that raise severity

If any of the following are true, overall risk increases:

1. Control API routes are reachable from untrusted networks without strong authentication.
2. Token controls are unset/reused broadly or secrets are stored in commit history, logs, or artifacts.
3. Compose/deployment publishes powerful services broadly without compensating controls.
4. Dependency and workflow supply-chain controls are not consistently enforced.
5. Powerful local management helpers are executed in mixed-trust environments without confirmation/guardrails.

## Non-overclaim statement

v101.1 security posture is **improving but incomplete**. Existing mitigations reduce specific risks, but planned controls and operational assumptions remain necessary for acceptable deployment risk.
