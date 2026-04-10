# Kernel Upgrade Phase 2 (Forky + 7.0 Family)

This Phase 2 document defines the 7.0-era kernel model used by this repository.
It replaces old pre-7.0 migration notes and removes legacy references
that are no longer operationally correct.

## Scope

Phase 2 now covers:

1. Aligning hosts to Debian 14 (Forky) kernel packaging assumptions.
2. Selecting the correct 7.0 family track (`base`, `core`, or `pulse`).
3. Using `7.0.0-rc7` only as the **lab-gateway** build for validation and
   cross-track promotion decisions.

## 7.0 Kernel Family Structure

The 7.0 era is organized as a family of roles rather than a single monolithic
kernel label.

### `base`

The conservative track for broad compatibility and lowest operational risk.
Use for general-purpose systems and default fleet rollouts.

### `core`

The production-optimized track for standard platform workloads after validation
on `base` and lab-gateway acceptance criteria are met.

### `pulse`

The fast-iteration track for feature velocity, tighter validation loops, and
short-cycle experimentation before changes graduate to `core`.

## Lab-Gateway Role of `7.0.0-rc7`

`7.0.0-rc7` is the 7.0-era **lab gateway**.

It is used to:

- qualify candidate changes early,
- exercise integration and hardware edge cases,
- decide readiness for promotion into supported family tracks.

It is **not** the default broad-deployment baseline for all hosts.

## Phase 2 Workflow (7.0 Era)

### K-01 — Forky alignment and baseline readiness

- Confirm the node is aligned with Forky-era package sources and kernel tooling.
- Verify the host can install and boot the selected 7.0 family artifacts.

### K-02 — Track selection and install (`base` / `core` / `pulse`)

- Assign each node a track according to its role.
- Install the corresponding 7.0 family kernel/config package set.
- Record the selected track in deployment metadata.

### K-03 — `7.0.0-rc7` lab-gateway qualification

- Run pre-promotion validation on `7.0.0-rc7` in lab-gateway environments.
- Capture regressions and stabilization deltas before production promotion.
- Promote only validated changes from lab-gateway outcomes into the relevant
  7.0 family track.

### K-04 — Post-upgrade service and policy verification

- Validate required services and boot-time policies after kernel transition.
- Ensure environment-specific masks/overrides are intentional and documented.

## Terminology and Legacy Status

- Pre-7.0 kernel naming language is retired from this Phase 2 procedure.
- Any remaining pre-7.0 references in the repository are historical context
  only and must not be interpreted as current upgrade guidance.

This file is the canonical Phase 2 reference for the Forky + 7.0 kernel era.
