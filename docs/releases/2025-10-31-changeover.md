# 2025-10-31 Changeover — Forky Standard • Kernel 7.0 Active Line • 7.0.0-rc7 Lab Gateway

## Summary
This changeover note supersedes the earlier `6.18.2-hueyos-v1` framing.

As of this release line:
- **Debian 14 "Forky" is the standard platform baseline** for project operations.
- **Kernel 7.0 is the active kernel line** for engineering, validation, and release tracking.
- **Kernel 7.0.0-rc7 is a lab gateway build only** (pre-production validation path), **not** the stable production baseline.

## What changed
- Platform posture updated from one-off migration messaging to **Forky-as-standard** messaging.
- Kernel guidance moved from `6.18.2-hueyos-v1` baseline language to **7.0 active-line governance**.
- `7.0.0-rc7` explicitly classified as a **lab/qualification entry point**, not production default.
- Release communications updated to avoid treating any `-rc` kernel as generally stable.

## Environment guidance
### Production
- Track the current approved **stable 7.0.x** target for production rollout.
- Do not use `7.0.0-rc7` as the default production kernel.

### Lab / validation
- Use `7.0.0-rc7` for gateway validation, compatibility triage, and pre-GA test sequencing.
- Promote to production only after stable 7.0.x approval gates are met.

## Upgrade steps (condensed)
1. Confirm hosts are on the Forky standard image/profile.
2. Move systems targeting legacy baseline language to the active 7.0 policy track.
3. Reserve `7.0.0-rc7` deployments for lab scopes.
4. Validate release notes, runbooks, and rollout checklists reference stable 7.0.x for production.

## Known issues
- Any reference that still describes `6.18.2-hueyos-v1` as the baseline should be treated as historical and updated.

## Rollback
- If a 7.0 trial fails validation, roll affected lab nodes back to the currently approved production stable kernel and re-enter qualification after remediation.
