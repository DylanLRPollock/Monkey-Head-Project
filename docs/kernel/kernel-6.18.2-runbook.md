# Historical Note: Linux 6.18.2 Migration (Legacy)

> **Status:** Legacy documentation for a completed migration.
> **Current guidance:** Do **not** use this as a live runbook for new hosts.

This document preserves the context of a past upgrade wave where HueyOS hosts
were moved to a DKMS-free `6.18.2-hueyos-v1` kernel with Apple CS8409 audio
support. It is retained as historical reference only.

## Why this note exists

The original `6.18.2` runbook was written as operational guidance during that
specific rollout. The environment, package baselines, and kernel assumptions
have since changed for the 7.0-era platform.

Treat all commands from the former runbook as **time-bound artifacts** rather
than current instructions.

## What was migrated in the 6.18.2 cycle

The completed migration generally included:

- Building and installing a custom `6.18.2-hueyos-v1` kernel.
- Preferring HDA/CS8409 in-kernel audio modules with SOF retained as fallback.
- Optional Secure Boot module-signing setup.
- Post-upgrade validation (`dmesg`, ALSA/PipeWire, sink verification).
- Supplemental Broadcom firmware sanity steps for affected iMac18,3 hosts.

## 7.0-era interpretation

For 7.0-era systems, this legacy migration should be interpreted as:

- A record of **what was changed historically**.
- A source of troubleshooting clues if you are diagnosing an old
  `6.18.2-hueyos-v1` installation.
- **Not** a baseline for present-day kernel build/deploy procedures.

If you need current procedures, use the active kernel/platform upgrade docs in
this repository and treat any 6.18.2-specific toggles, blacklists, and firmware
symlinks as potentially obsolete.

## Legacy markers to watch for

If these appear on a machine, you are likely looking at a host that followed
this historical path:

- Kernel release string matching `6.18.2-hueyos-v1`.
- Modprobe snippets that explicitly blacklist SOF to force HDA.
- Manually created Broadcom firmware symlinks for Apple iMac18,3 naming.

## Preservation policy

This file intentionally remains short and historical so it no longer reads as
current guidance while still documenting the intent and scope of the 6.18.2
migration.
