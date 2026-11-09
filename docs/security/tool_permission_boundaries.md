# Tool and Plugin Permission Boundaries (PyHuey/MonkeyManager)

This note describes the current implementation and remaining boundaries for
`huey.connectors.pyhuey.tools.manager.MonkeyManager`.

## Current implementation

The checked-in MonkeyManager module is currently a minimal cockpit stub with no
script, container, Kubernetes, browser, or provider execution methods. Older
notes about `_run_script()` and `HUEY_TOOL_ALLOW_DESTRUCTIVE` describe an
previous implementation and must not be treated as current enforcement.

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

## Remaining boundary

This policy does not authenticate the `actor_role` argument for arbitrary
in-process callers. API ingress maps credentials to roles before reaching the
gate; local callers must be trusted and must not forward untrusted role claims.
The named-credential option provides configured attribution, not external identity
verification or federated login. Shared legacy tokens still collapse callers to
one subject. Task ownership, tamper-resistant action records, trusted-proxy
policy, and fine-grained container/agent capabilities remain absent. Direct
in-process actions are not covered by the HTTP action log.

The UI stub exposes no privileged actions at present. If script, container,
Kubernetes, or tool execution is added, route every mutating operation through
the shared gate, validate paths and argv, set timeouts, and test that denied
requests launch no subprocess and touch no filesystem.
