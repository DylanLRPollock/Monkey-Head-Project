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
| `/power/shutdown` | Requires admin-scoped token and exact `X-Huey-Confirm: shutdown`. | Strongest ingress gate; no actor identity beyond role. |
| Task submit/cancel | Authenticated when the default scheduler or API tokens are active; free-form submission has separate unsafe-task gating. | Caller identity and per-task ownership are not enforced. |
| `/network/ensure`, `/memory/auto-sort` | Explicit strong bearer authentication. | Role is authenticated but currently not narrowed beyond operator/admin. |
| Emergency governance writes | Strong auth when the default controller or tokens are active; controller validates approval count. | `actor`, `triggered_by`, `requested_by`, and `approvals` are request claims, not verified people. |
| Sensor registration/removal/poll; resilience restart/override; admin service start/stop; other POST routes | Protected by global bearer middleware when configured; local development can run without configured credentials. | No route-specific admin policy. Every configured bearer role can reach the same writes except shutdown. |
| Direct library host actions | Local intent/confirmation gate and deny-by-default policy. | `actor_role` is a caller claim when invoked outside authenticated API ingress. |
| Plugins, agent tools, command center | Inspected by source and current tests. | A complete capability registry and per-user audit trail do not yet exist; command-center endpoints are read-only. |

## Mutating route inventory

The current HTTP mutation surface includes task submission/cancellation;
network connectivity checks; power shutdown; sensor registration, removal,
and polling; resilience override, restart, poll, and watchdog ping; memory
auto-sort; emergency enter/exit/action; service start/stop; system checks; and
text processing/analysis operations. `GET` routes include status, telemetry,
history, model, PDF, and process listings. The global token middleware protects
all non-health routes only when credentials have been configured; it does not
provide route-specific privileges.

## Release decision and follow-up requirements

- No code path found in this audit grants admin from a body/query actor string;
  shutdown’s role comes from bearer-token matching.
- Do not describe this deployment as per-user authenticated or audited.
- Before remote multi-user operation, replace shared tokens with individually
  named credentials or an external identity provider, enforce route-level role
  policies (admin for service lifecycle, registration/removal, restart, and
  host shutdown), add owner checks for task operations, and emit secret-free
  audit records containing principal, role, action, target, outcome, and UTC
  time.
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
