# HueyOS Documentation

HueyOS combines robotics control, knowledge management, and constitutional
governance primitives. The documents in this directory explain how to extend
the platform and how to operate core services.

## Quick starts

- [CLI quick reference](#cli-quick-reference)
- [Sensor plugin development](sensor-plugins.md)
- [Honeycomb storage operations](honeycomb-storage.md)
- [API reference](api-reference.md)
- [Governance & resilience](governance.md)
- [Kernel 7.0 Phase 2 runbook (active guidance)](kernel-upgrade-phase2.md)
- [Linux 6.18.2 migration runbook (legacy archive)](kernel-6.18.2-runbook.md)
- [Version reference classification report](version-reference-classification.md)
- [Phase 9 rollback hooks report](phase-9-rollback.md)

## CLI quick reference

```bash
huey run --ml --cloud             # launch runtime with ML + cloud profiles
huey system-check --verbose       # detailed diagnostics
huey deploy --mode docker         # docker-only deployment
huey agent-status --json          # scheduler snapshot as JSON
huey memory-sort --dry-run --json # dry-run memory organiser
```
