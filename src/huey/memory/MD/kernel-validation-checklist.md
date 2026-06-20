# Kernel Validation Checklist

Use this checklist before merging kernel-facing or platform-string changes.

## 1) Baseline and naming validation

- [ ] Confirm active guidance remains on the 7.0 active-line baseline (not migration-era naming).
- [ ] Run `python scripts/repo/check_stale_platform_strings.py` and verify no new stale strings were added outside approved legacy/archive paths.
- [ ] If historical references are necessary, store them only in approved legacy/archive paths and label them as historical context.

## 2) Build/config validation

- [ ] Validate the assembled kernel config still succeeds:
  - `bash kernel/assemble_kernel_config.sh`
- [ ] If fragment files changed, confirm expected options in the assembled output and note any intentional deltas.
- [ ] If release naming or boot logic changed, validate install/update helper scripts still parse expected values.

## 3) Runtime sanity checks

- [ ] Boot and confirm kernel release string is the expected active target.
- [ ] Verify platform checks in application startup continue to pass (`src/hueyos/system_checks.py`, `src/huey/main.py`).
- [ ] Run the relevant smoke checks for services that depend on kernel capabilities (storage, sensors, graphics, virtualization).

## 4) Test and CI checks

- [ ] Run `make lint`.
- [ ] Run `make test` (or targeted tests when working in constrained environments).
- [ ] Ensure CI passes on pull request and any kernel-related warning is either fixed or documented in the PR.

## 5) Documentation and release hygiene

- [ ] Update active runbooks/docs if behavior changed.
- [ ] Keep legacy migration notes in historical docs only.
- [ ] Add a release note entry describing kernel-facing impacts, rollback notes, and operator action items.
