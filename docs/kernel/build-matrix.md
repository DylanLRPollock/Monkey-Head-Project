# Kernel Build Matrix (Core / Pulse / Lab / ISO / Recovery-Install)

This matrix is the canonical quick-reference for which kernel **roles** and
**name variants** are valid in each build or boot flow.

Use this to keep automation, release notes, and future Codex updates aligned
with the 7.0 role model.

## Canonical role set

Only these role keys are valid for role-aware build tooling:

- `core`
- `pulse`
- `lab`

The kernel config assembly scripts enforce this exact set and reject any other
role string (`base`, `iso`, `recovery`, etc.) as a role input.

## Naming variants

### Canonical artifact-style names (preferred in docs/releases)

- `7.0.0-hueyos-core`
- `7.0.0-hueyos-pulse`
- `7.0.0-rc7-hueyos-lab`

### Accepted short role aliases (tooling input)

- `core`
- `pulse`
- `lab`

### Invalid naming examples

- `7.0.0-hueyos-lab` (lab is tied to `-rc7` gateway naming in current guidance)
- `7.0.0-rc7-hueyos-core`
- `7.0.0-rc7-hueyos-pulse`
- any role token outside `core|pulse|lab`

## Build / flow matrix

| Build or flow | Valid kernel role(s) | Valid naming variant(s) | Notes |
| --- | --- | --- | --- |
| Core build | `core` | `core`; `7.0.0-hueyos-core` | Production-oriented role. |
| Pulse build | `pulse` | `pulse`; `7.0.0-hueyos-pulse` | Fast-iteration/control-oriented role. |
| Lab build | `lab` | `lab`; `7.0.0-rc7-hueyos-lab` | Lab-gateway and pre-promotion validation only. |
| ISO build | `core`, `pulse`, or `lab` (selected profile) | Must preserve selected role naming (`...-core`, `...-pulse`, or `...-rc7-...-lab`) | `iso` is a packaging format/flow, not a kernel role. |
| Recovery flow | `core`, `pulse`, or `lab` (match the target system policy) | Same role naming as the recovery target | `recovery` is an operational path, not a role token. |
| Install flow | `core`, `pulse`, or `lab` (match install intent) | Same role naming as the selected deployment role | `install` is an operational path, not a role token. |

## Guardrails for future edits

1. Do not introduce new role tokens without updating both role assembly scripts
   and this matrix.
2. Treat `iso`, `recovery`, and `install` as flow labels only.
3. Keep lab naming tied to the lab-gateway form (`7.0.0-rc7-hueyos-lab`) unless
   release policy formally changes.
4. When in doubt, normalize to lowercase role keys in tooling and reserve
   title-case words (`Core`, `Pulse`, `Lab`) for prose headings.
