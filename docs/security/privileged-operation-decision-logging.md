# Privileged operation decision logging

The shared deny-by-default gate in
`src/huey/os/core/privileged_operations.py` emits one JSON log record for
each registered operation decision: allowed, denied, or dry-run. This also
covers direct library callers that do not pass through the HTTP API middleware.

Each record includes:

- UTC timestamp, event name, registered operation, and capability class.
- The role claim supplied to the local gate, or `unrecognized` when the value
  is not one of the supported role strings.
- Explicit-confirmation and dry-run flags, outcome, and a fixed reason code.

Records do not include bearer credentials, command arguments, filesystem paths,
or request bodies. Unknown operation names are represented as
`unregistered`; the caller-provided string is not included in the log.

The role field records a caller claim. It does not verify a person or service
identity. HTTP routes may also produce their own request-level mutation record,
so a single HTTP action can have both an ingress record and a capability-gate
record. Events go to the application's configured Python logger; this does not
provide durable storage, tamper resistance, centralized collection, or
guaranteed retention. Deployments requiring those properties must configure an
external protected log sink.

This change does not add per-task ownership, identity federation, or a complete
third-party plugin/agent capability registry. Those remain tracked under
[issue #852](https://github.com/DylanLRPollock/Monkey-Head-Project/issues/852).
