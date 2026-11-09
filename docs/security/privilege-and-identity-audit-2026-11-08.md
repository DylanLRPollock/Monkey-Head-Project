# Privilege and identity audit (2026-11-08)

## Scope and result

Reviewed FastAPI ingress in `src/huey/memory/PY/api.py` and
`src/huey/os/api/routers/`, plus the repository’s host-action, scheduler,
plugin, and agent boundaries. This is an implementation audit; constitutional
roles and caller-supplied actor names are not treated as authenticated identity.

## Current controls

| Surface | Current control | Finding |
| --- | --- | --- |
| `/healthz` | Public health-only exception | No sensitive data observed in response. |
| Other HTTP routes | If any API token is configured, global middleware requires a valid bearer token; with no token configured, non-health ingress is loopback-only. | Tokens are shared secrets and have no subject, expiry, individual revocation, or attribution. A public reverse proxy must enforce authentication itself. |
| `HUEY_API_TOKEN` | Treated as operator scope; dedicated operator/admin variables are also supported. | Compatibility token remains broad API access. |
| Operator/admin credential separation | Configuration rejects an admin token equal to either operator token. | Prevents a shared credential from being upgraded to admin by role lookup. |
| `/power/shutdown` | Requires admin-scoped token and exact `X-Huey-Confirm: shutdown`; loopback-only development mode is retained when no tokens are configured. | No actor identity beyond role. |
| Task submit/cancel | Authenticated when the default scheduler or API tokens are active; free-form submission has separate unsafe-task gating. | Caller identity and per-task ownership are not enforced. |
| `/network/ensure`, `/memory/auto-sort` | Admin-scoped token; loopback-only development mode when no tokens are configured. | No named principal or action audit trail. |
| Emergency governance writes | Strong auth when the default controller or tokens are active; controller validates approval count. | `actor`, `triggered_by`, `requested_by`, and `approvals` are request claims, not verified people. |
| Sensor registration/removal; resilience restart/override; service start/stop | Admin-scoped token; loopback-only development mode when no tokens are configured. | Polling and watchdog actions remain operator-scoped through global bearer auth. |
| Emergency governance enter/exit/action | Admin-scoped token when auth is configured; approval counts remain controller-validated. | Approval names are still caller claims and do not identify distinct authenticated people. |
| Other POST routes | Global bearer middleware when credentials are configured; otherwise loopback-only. | Read-like processing and telemetry operations share the same global operator token; task ownership is not implemented. |
| Direct power, uninstall, install, update, account, command execution, failover, Docker, and Kubernetes operations | Shared deny-by-default capability gate. Mutating/destructive calls require explicit confirmation and role; dry-run returns before host/path access. GUI container actions prompt, CLI install/cluster/arbitrary command actions require `--yes`, and PyGPT manager mutating actions require explicit process opt-in. | Local `actor_role` values and environment opt-ins are intent claims, not named identity. OS privilege checks remain a separate boundary. |
| Container and cluster helpers | Direct public helpers enforce capability gates, use argv with `shell=False` and timeouts, validate Kubernetes manifests and scale names, and reject invalid Docker tags. The legacy import path re-exports these canonical guarded helpers. Volume/network manager actions only list resources; pruning was removed from those actions. | Docker/Kubernetes command completion still depends on local tool policy and credentials. No per-user action audit trail exists. |
| Plugins, agent tools, command center | Built-in PyGPT manager commands are capability-gated; command-center endpoints remain read-only. | A complete plugin/agent capability registry and per-user audit trail do not yet exist. Third-party tools need their own review. |

## Mutating route inventory

The current HTTP mutation surface includes task submission/cancellation;
network connectivity checks; power shutdown; sensor registration, removal,
and polling; resilience override, restart, poll, and watchdog ping; memory
auto-sort; emergency enter/exit/action; service start/stop; system checks; and
text processing/analysis operations. Admin scope is required for the
host-affecting and configuration-mutating operations listed in the table above.
Task submission/cancellation, polling, and selected read-like POST operations
remain operator-scoped. `GET` routes include status, telemetry, history, model,
PDF, and process listings. Direct library and GUI/container entrypoints are
guarded separately by the local capability gate.

## Release decision and follow-up requirements

- No code path found in this audit grants admin from a body/query actor string;
  shutdown’s role comes from bearer-token matching.
- Do not describe this deployment as per-user authenticated or audited.
- Before remote multi-user operation, replace shared tokens with individually
  named credentials or an external identity provider, add owner checks for task
  operations, and emit secret-free audit records containing principal, role,
  action, target, outcome, and UTC time.
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
