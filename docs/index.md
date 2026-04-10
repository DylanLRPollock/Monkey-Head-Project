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
- [Linux 6.18.2 migration note (legacy archive)](kernel-6.18.2-runbook.md)
- [Kernel upgrade Phase 2 runbook (7.0 active line)](kernel-upgrade-phase2.md)
- [Phase 9 rollback hooks report](phase-9-rollback.md)
- [6.18.2 reference classification](version-reference-classification.md)

## CLI quick reference

```bash
huey run --ml --cloud             # launch runtime with ML + cloud profiles
huey system-check --verbose       # detailed diagnostics
huey deploy --mode docker         # docker-only deployment
huey agent-status --json          # scheduler snapshot as JSON
huey memory-sort --dry-run --json # dry-run memory organiser
```
