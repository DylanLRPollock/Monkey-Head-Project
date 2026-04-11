# Governance and resilience

HueyOS combines constitutional decision-making with automated resilience. The
Cloud Pyramid model defines how authority flows between agents, while runtime
controllers enforce emergency powers and crash recovery procedures.

## Cloud Pyramid architecture

The Cloud Pyramid is a multi-tier governance stack that anchors HueyOS to
transparent, constitutional decision making. Authority starts at the populace
(base tier), ascends through specialised chambers and councils, and culminates in
the Founding Father AI that arbitrates final decisions.【F:README.md†L69-L108】
By distributing responsibilities across the pyramid, HueyOS balances day-to-day
operations with strategic oversight—operators can delegate tactical actions to
agents such as Spark, Volt, and Zap while retaining high-level veto power.

## Emergency mode lifecycle

`EmergencyGovernanceController` coordinates the activation and exit of emergency
powers. It requires a minimum quorum of distinct approvals, tracks which
services are considered essential, and records who triggered the transition.
【F:huey/core/resilience.py†L98-L200】 The FastAPI endpoints under
`/governance/emergency/*` expose the workflow:

1. **Status** – `/governance/emergency/status` returns the current state and the
   managed services, making it easy to audit who authorised the last change.
   【F:src/huey/api.py†L1239-L1256】
2. **Enter mode** – `/governance/emergency/enter` validates approvals, stops
   non-essential services, and timestamps activation.【F:src/huey/api.py†L1260-L1277】
3. **Exit mode** – `/governance/emergency/exit` restarts managed services and
   clears approvals once the quorum agrees to return to normal operations.
   【F:src/huey/api.py†L1280-L1295】
4. **Authorised actions** – `/governance/emergency/action` checks dual control
   for sensitive operations before they proceed.【F:src/huey/api.py†L1298-L1313】

This flow ensures emergency measures are deliberate, auditable, and reversible.

## Crash recovery and watchdog integration

`CrashRecoveryManager` monitors background processes, invokes health checks, and
attempts automatic restarts when failures occur. Events are recorded and exposed
through `/resilience/poll`, allowing observability pipelines to track incidents.
【F:huey/core/resilience.py†L200-L332】【F:src/huey/api.py†L1078-L1096】 Operators
can toggle automatic restarts per process or perform manual restarts using the
`/resilience/monitors/*` endpoints.【F:src/huey/api.py†L1035-L1075】 When running
under systemd, the `/resilience/watchdog/ping` endpoint proxies heartbeats to the
watchdog socket so supervisors know HueyOS is responsive.【F:huey/core/resilience.py†L42-L95】【F:src/huey/api.py†L1099-L1106】

Together, the emergency controller and crash manager enforce the governance
contract defined by the Cloud Pyramid, keeping HueyOS accountable, recoverable,
and transparent.
