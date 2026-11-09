# Privilege and identity audit (reviewed 2026-11-09)

## Scope and result

Reviewed FastAPI ingress in `src/huey/memory/PY/api.py` and
`src/huey/os/api/routers/`, plus the repository’s host-action, scheduler,
plugin, and agent boundaries. This is an implementation audit; constitutional
roles and caller-supplied actor names are not treated as authenticated identity.

## Current controls

| Surface | Current control | Finding |
| --- | --- | --- |
| `/healthz` | Public health-only exception | No sensitive data observed in response. |
| Other HTTP routes | If any API token is configured, global middleware requires a valid bearer token; with no token configured, non-health ingress is loopback-only. | Named JSON credentials carry a configured subject and role; compatibility tokens remain shared. There is no external identity provider or token expiry. A public reverse proxy must enforce authentication itself. |
| API credentials | `HUEY_API_TOKEN` and dedicated operator/admin variables remain supported; `HUEY_API_PRINCIPALS_JSON` adds individually named operator/admin credentials. | Shared-token clients still have aggregate identity; named subjects are configured locally, not asserted by an external identity provider. |
| Operator/admin credential separation | Configuration rejects duplicate credential values, and named principals require unique subjects/tokens and explicit operator/admin roles. | Prevents credential reuse from creating ambiguous identity or privilege escalation. |
| `/power/shutdown` | Requires admin-scoped credential and exact `X-Huey-Confirm: shutdown`; loopback-only development mode is retained when no tokens are configured. | Named credentials are attributable by configured subject; shared tokens remain shared and loopback identity is explicitly unverified. |
| Task submit/list/get/cancel | API submissions are assigned the authenticated principal's subject. Operators can list, read, or cancel only their own tasks; admins can access all tasks. | Legacy shared credentials and loopback development access aggregate callers under one subject. Direct in-process scheduler calls are outside this HTTP ownership boundary. |
| `/network/ensure`, `/memory/auto-sort` | Admin-scoped credential; loopback-only development mode when no credentials are configured. | Mutating API requests emit secret-free application log records with subject/role, route template, result status, and UTC time. Logs are not tamper-resistant audit storage. |
| Emergency governance writes | Strong auth when the default controller or tokens are active; controller validates approval count. | `actor`, `triggered_by`, `requested_by`, and `approvals` are request claims, not verified people. |
| Sensor registration/removal; resilience restart/override; service start/stop | Admin-scoped token; loopback-only development mode when no tokens are configured. | Polling and watchdog actions remain operator-scoped through global bearer auth. |
| Emergency governance enter/exit/action | Admin-scoped token when auth is configured; approval counts remain controller-validated. | Approval names are still caller claims and do not identify distinct authenticated people. |
| Other POST routes | Global bearer middleware when credentials are configured; otherwise loopback-only. | Named principal attribution applies to API request logs. Routes outside task management do not have per-user object ownership. |
| Direct power, uninstall, install, update, account, diagnostics, failover, Docker, and Kubernetes operations | Shared deny-by-default capability gate. Mutating/destructive calls require explicit confirmation and role; dry-run returns before host/path access. Gate decisions now emit secret-free structured application logs. | Local `actor_role` values and environment opt-ins remain caller claims, not named identity. Logs are not durable or tamper-resistant, and OS privilege checks remain separate. |
| Container and cluster helpers | Direct public helpers enforce capability gates, use argv with `shell=False` and timeouts, validate Kubernetes manifests and scale names, and reject invalid Docker tags. The legacy import path re-exports these canonical guarded helpers. Volume/network manager actions only list resources; pruning was removed from those actions. | Docker/Kubernetes command completion still depends on local tool policy and credentials. Direct gate events are logged with a claimed role, not a verified principal, and need a protected external sink for durable retention. |
| Plugins, agent tools, command center | Built-in PyHuey manager commands are capability-gated; command-center endpoints remain read-only. | A complete plugin/agent capability registry and per-user verified audit identity do not yet exist. Third-party tools need their own capability review. |

## Named principal configuration and audit logging

Production can authenticate named API credentials without requiring the legacy
shared token. Set `HUEY_API_PRINCIPALS_JSON` to a JSON array whose entries
contain a unique `subject`, an `operator` or `admin` role, and a unique
`token`. Alternatively, the existing shared token variables remain supported.
The application logs mutating HTTP route templates, configured subject/role,
response status, and UTC time; authorization failures are also logged without
recording bearer values or request bodies. The shared privileged-operation
gate also records direct in-process authorization decisions with operation,
capability, claimed role, confirmation flags, outcome, reason, and UTC time.

A configured subject is a local credential label, not proof of a human identity
from an external identity provider. Shared credentials map to a shared subject;
loopback development access uses one unverified local subject. Task API
submissions carry the authenticated subject, and operators can list, read, or
cancel only their own tasks; admins can access all tasks. Tasks created through
direct scheduler calls are outside this HTTP ownership boundary.

HTTP and privileged-operation events go to ordinary application logs, not
append-only or tamper-resistant audit storage. Caller-attributed emergency
approvals and a complete plugin/agent capability registry remain open controls.

## Mutating route inventory

The current HTTP mutation surface includes task submission/cancellation;
network connectivity checks; power shutdown; sensor registration, removal,
and polling; resilience override, restart, poll, and watchdog ping; memory
auto-sort; emergency enter/exit/action; service start/stop; system checks; and
text processing/analysis operations. Admin scope is required for the
host-affecting and configuration-mutating operations listed in the table above.
Task submission requires the configured unsafe-task opt-in and an authenticated
principal; task list/detail/cancel access is owner-scoped for operators and
cross-owner for admins. Polling and selected read-like POST operations remain
operator-scoped. `GET` routes include status, telemetry, history, model, PDF,
and process listings. Direct library and GUI/container entrypoints are
guarded separately by the local capability gate.

## Release decision and follow-up requirements

- No code path found in this audit grants admin from a body/query actor string;
  shutdown’s role comes from bearer-token matching.
- Do not describe this deployment as externally user-authenticated or as a
  tamper-resistant audit system. Named subjects are locally configured labels;
  shared credentials still aggregate clients to one subject.
- Before remote multi-user operation, replace shared credentials with an
  external identity provider if independently verified identities are required.
  Configure a protected external sink if durable audit retention is required.
  Complete the plugin/agent capability registry and authenticate any third-party
  tools that perform privileged actions.
- Preserve local development behavior only as an explicit loopback policy;
  verify proxy deployments do not trust forwarded client addresses.
- Continue treating plugin/agent execution as a separate capability boundary;
  API authentication alone does not constrain what a plugin can do after it is
  loaded.

## Verification evidence

The audit is backed by the route definitions, token middleware and scoped-token
helpers in `src/huey/memory/PY/api.py`, extracted routers in
`src/huey/os/api/routers/`, and API tests in `tests/test_api_routes.py`. This
document describes current source behavior and is not a deployment attestation.

The direct-operation safeguards summarized above were merged in PR #870 on
2026-11-09. Named API credential attribution and secret-free mutation logging
are implemented in the current change. Per-task ownership, external identity
verification, tamper-resistant audit storage, direct in-process action logging,
and a complete plugin/agent capability registry remain open.
