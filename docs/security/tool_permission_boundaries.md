# Tool and Plugin Permission Boundaries (PyHuey/MonkeyManager)

This note describes the current implementation and remaining boundaries for
`huey.connectors.pyhuey.tools.manager.MonkeyManager`.

## Current implementation

Core HueyOS host power and project uninstall operations use
`huey.os.core.privileged_operations.authorize_privileged_operation`:

- Unknown operations are denied.
- Destructive operations require explicit confirmation and the `admin` role.
- Mutating operations require explicit confirmation and `operator` or `admin`.
- Dry-run returns before platform discovery, filesystem probing, or subprocess
  launch.
- Power commands are constructed from fixed platform-specific argv lists with
  `shell=False`; the uninstaller verifies the resolved script remains inside
  the project root and uses a timeout.
- API credentials can be configured as shared role tokens through
  `HUEY_API_OPERATOR_TOKEN` / `HUEY_API_ADMIN_TOKEN`, with legacy
  `HUEY_API_TOKEN` remaining operator-scoped, or as unique named credentials
  in `HUEY_API_PRINCIPALS_JSON`. Named principals receive configured
  operator/admin roles and are attached to request state. Host shutdown also
  requires the `X-Huey-Confirm: shutdown` header and admin scope.
- Mutating HTTP requests produce secret-free application log entries with
  principal label, role, route template, outcome status, and UTC time.
- PyHuey's `MonkeyManager` routes install, update, run, container, Kubernetes,
  and memory auto-sort actions through the same capability gate. Its optional
  host-supplied authorization provider returns a verified role and explicit
  confirmation for each operation. Without that provider, manager actions are
  denied; `HUEY_TOOL_ALLOW_MUTATING` and `HUEY_TOOL_ALLOW_DESTRUCTIVE` are not
  authorization mechanisms. Manager construction and dry-run decisions do not
  resolve project paths or scan registered functions.
- Manager script execution resolves the script path, rejects symlinks and
  paths outside the project root, and runs an argv list with `shell=False` and
  a 300-second timeout. Mutating registered functions are capability-gated
  before invocation; only reviewed registry functions are exposed, with
  read-only functions requiring the `reader` role.

## Remaining boundary

This policy does not authenticate the `actor_role` argument for arbitrary
in-process callers. API ingress maps credentials to roles before reaching the
gate. The PyHuey authorization provider is a trusted host integration point;
it must establish caller identity and obtain confirmation rather than
forwarding request-derived role claims.
The named-credential option provides configured attribution, not external identity
verification or federated login. Shared legacy tokens still collapse callers to
one subject. Task ownership, tamper-resistant action records, trusted-proxy
policy, and external identity federation remain absent. Direct in-process
actions are not covered by the HTTP action log.

## Migration impact

The prior `HUEY_TOOL_ALLOW_MUTATING=1` and
`HUEY_TOOL_ALLOW_DESTRUCTIVE=1` environment opt-ins no longer authorize
MonkeyManager actions. Integrations that need those actions must construct the
manager with an authorization provider that validates a role for each
capability and returns explicit confirmation when required. Existing scripts
and container functions continue to deny direct calls unless their caller
supplies the required role and confirmation.
