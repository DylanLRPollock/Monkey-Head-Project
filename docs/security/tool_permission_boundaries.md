# Tool and Plugin Permission Boundaries (PyHuey/MonkeyManager)

This note describes the current implementation and remaining boundaries for
`huey.connectors.pyhuey.tools.manager.MonkeyManager`.

## Current implementation

The checked-in MonkeyManager module is currently a minimal PyGPT stub with no
script, container, Kubernetes, browser, or provider execution methods. Older
notes about `_run_script()` and `HUEY_TOOL_ALLOW_DESTRUCTIVE` describe a
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
- API tokens are scoped: `HUEY_API_OPERATOR_TOKEN` and
  `HUEY_API_ADMIN_TOKEN` provide separate roles. The legacy `HUEY_API_TOKEN`
  remains accepted as an operator token. Host shutdown also requires the
  `X-Huey-Confirm: shutdown` header and an admin-scoped token.

## Remaining boundary

This policy does not authenticate the `actor_role` argument for arbitrary
in-process callers. API ingress maps credentials to roles before reaching the
gate; local callers must be trusted and must not forward untrusted role claims.
The token scheme does not yet provide per-user identities, audit attribution,
trusted-proxy policy, or fine-grained container/agent capabilities. Do not
present those controls as implemented until a separate authenticated principal
model and connector/action audit are in place.

The UI stub exposes no privileged actions at present. If script, container,
Kubernetes, or tool execution is added, route every mutating operation through
the shared gate, validate paths and argv, set timeouts, and test that denied
requests launch no subprocess and touch no filesystem.
