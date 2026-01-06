# Security Policy

**Project:** Monkey-Head-Project (**HueyOS**)
**Last updated:** 2026-01-06

HueyOS takes security seriously. This policy explains what we support, how to report issues, and how we coordinate fixes, backports, releases, and disclosure across the project’s **on-robot runtime**, **helper tools**, and **reference deployments**.

HueyOS is typically deployed as an **offline-first**, self-hosted system with tightly scoped network surfaces. Even so, we treat every externally reachable interface (HTTP APIs, admin consoles, message queues, IPC endpoints, artifact pipelines, etc.) as potentially hostile and design our security posture accordingly.

---

## Supported Versions

HueyOS uses semantic versioning (`MAJOR.MINOR.PATCH`):

* **MAJOR:** Structural or incompatible changes to APIs, storage, or governance assumptions.
* **MINOR:** Backward-compatible feature releases and roadmap milestones.
* **PATCH:** Bugfix and security releases only.

### Support window

Security support normally covers:

* **Current MINOR line** (e.g., `0.3.x`)
* **Previous MINOR line** (e.g., `0.2.x`)

Older versions are **unsupported** unless explicitly noted in a security advisory (for example, if an older line is widely deployed and warrants a one-off fix).

> The table below is illustrative and is updated when new releases are cut and tagged.

| Version / Line          | Status                           |
| ----------------------- | -------------------------------- |
| `0.3.x` (current)       | ✅ Actively supported             |
| `0.2.x` (previous)      | 🔶 Critical fixes only           |
| `< 0.2.0`               | ❌ Unsupported                    |
| `main` (default branch) | ✅ Fixes land here before release |

**Notes**

* Security fixes typically land on `main` first and are then **backported** to supported minor lines as appropriate.
* Development and feature branches are **not** covered by this policy; they may contain experimental or partially hardened code.
* Downstream forks/distributions should document the upstream version/commit they track and define their own support window.

---

## Supported Platforms

### Runtime environment

HueyOS is designed and tested primarily against:

* **OS**

  * Debian 13 “Trixie” (stable) — **primary supported** platform.
  * Debian 14 “Forky” — **staging/preview** only until explicitly promoted in release notes.
* **Architecture**

  * `amd64` (x86_64). Other architectures (ARM, RISC‑V, etc.) may work, but are currently out of scope for security guarantees.
* **Kernel**

  * HueyOS tracks Linux LTS or near-LTS kernels with project-specific configuration (e.g., `6.x-huey*`).
  * The supported kernel series per release are documented in that release’s notes/changelog.

### Virtualization and containers

* Running HueyOS in containers (Docker/Podman) or VMs (KVM/VirtualBox) is supported **as long as** the underlying host matches the OS/arch/kernel assumptions above.
* Container images and `docker-compose` files provided in this repository are **in scope**. Host misconfiguration outside documented recommendations is not.

---

## Reporting a Vulnerability

We strongly prefer **coordinated vulnerability disclosure**. Please report vulnerabilities privately and include enough information to reproduce and assess impact.

### Private reporting channels

1. **GitHub — Private Vulnerability Report (preferred)**
   Repository → **Security** tab → **Report a vulnerability**
   This records the report privately and supports coordinated fixes and advisories.

2. **Email**

   * Address: **[admin@dlrp.ca](mailto:admin@dlrp.ca)**
   * Subject: `VULN: <short title>`
   * If you require encryption, say so in your first email (e.g., “Please send your PGP key”). We will reply with a public key and instructions.

If you are unsure whether something qualifies as a vulnerability, report it privately anyway; we can help classify it.

### What to include

The more detail you can safely provide, the faster we can triage:

* **Summary** of the issue and its **security impact** (e.g., “unauthenticated RCE via …”).
* **Reproduction / PoC**, including:

  * Exact commands, HTTP requests, payloads, and expected/observed results.
  * Relevant configuration (`huey.env`, `docker-compose.yml`, systemd units), with secrets redacted.
  * Environment prerequisites (hardware, optional modules, external services).
* **Affected versions/commits and environment**

  * HueyOS version(s), Git commit hash, or branch.
  * OS, architecture, kernel version.
  * Non-default dependencies/services in play.
* Any **workarounds/mitigations** you’ve identified.
* Preferred **credit** (name/handle/link) or a note if you prefer anonymity.

### Please do not disclose publicly first

Avoid opening public GitHub issues, discussions, or pull requests that contain exploit details, sensitive stack traces, or configuration dumps until we have agreed on a disclosure timeline.

If you believe an issue is **actively exploited** or involves **credential leakage**, call that out clearly in the report subject/body so we can prioritize accordingly.

---

## Triage, Severity, and Response Targets

We use **CVSS v3.1** as a starting point for severity, combined with contextual factors (deployment mode, default configuration, and reachability in typical HueyOS setups).

### Target timelines (best-effort)

* **Acknowledgement:** within **72 hours** of receiving the report.
* **Initial triage & severity assessment:** within **7 calendar days**.
* **Fix/mitigation targets** (from acknowledgement):

  * **Critical (CVSS ≥ 9.0):** aim for a fix or robust mitigation within **14–21 days**
  * **High (7.0–8.9):** aim for mitigation and/or patch within **21–30 days**
  * **Medium (4.0–6.9):** aim for a fix or recommended mitigation within **30–60 days**
  * **Low (< 4.0):** scheduled based on impact, complexity, and capacity

These are targets, not guarantees. Complex issues, upstream dependencies, or hardware-specific problems may require more time; conversely, actively exploited issues may be resolved faster.

### Triage process

During triage, we typically:

1. **Reproduce** the issue in a controlled environment, mirroring the reporter’s setup where possible.
2. **Confirm impact and scope**, including prerequisites, privileges, and realistic exploitation paths.
3. **Assign provisional severity** (CVSS v3.1 + contextual risk).
4. **Identify affected versions** and any relevant reference deployments.
5. **Plan remediation**, including:

   * Short-term mitigations (config changes, ACLs, firewall guidance)
   * Longer-term patches (code, architecture, docs)
6. **Communicate** findings and next steps to the reporter.

### Communication cadence

For each valid security report, we aim to:

* Provide **weekly updates** while an issue remains open, or more frequently around milestones (reproduction, patch ready, release scheduled).
* Before publication, share:

  * Planned release/disclosure timing
  * High-level remediation notes and recommended operator actions
* After publication, share:

  * Link to the advisory
  * Final affected/fixed versions
  * Credit details (if requested)

### Severity reference

| Severity | CVSS (v3.1) |
| -------: | ----------- |
| Critical | 9.0–10.0    |
|     High | 7.0–8.9     |
|   Medium | 4.0–6.9     |
|      Low | 0.1–3.9     |

If your assessment differs (e.g., due to deployment realities we may have missed), share your reasoning and we will re-evaluate.

---

## Coordinated Disclosure and Embargo

Our default stance is responsible disclosure with sufficient time for users to patch.

* **Default embargo window:** **90 days** from acknowledgement.
* We may **shorten the embargo** if:

  * There is credible evidence of active exploitation
  * The vulnerability is trivially exploitable and widely exposed by default
  * A fix/mitigation is available and simple to deploy
* We may **extend the embargo** by mutual agreement if:

  * The issue is complex and requires substantial architectural change
  * Upstream fixes or multi-party coordination are required

### Advisory publication and CVEs

* Advisories are published via **GitHub Security Advisories** for this repository.
* For qualifying issues, we will **request a CVE** and reference it in the advisory, release notes, and documentation.
* Credit is included with the reporter’s permission (anonymous/pseudonymous credit supported).

If you intend to publish your own write-up, please coordinate timing with us so users have access to patches or mitigations when details become public.

---

## Fix, Backport, and Release Policy

When a vulnerability is confirmed:

1. **Patches are developed and reviewed** (on a private/restricted branch when appropriate).
2. Fixes merge to `main` first, then (where feasible) are:

   * **Backported** to all supported minor lines
   * Evaluated for backporting to older lines if widely deployed and risk is high
3. We cut **security releases** per maintained line:

   * Security releases increment `PATCH` (e.g., `0.3.4` → `0.3.5`)
   * Release notes clearly indicate security fixes

Each security release includes:

* Summary of the vulnerability (or multiple vulnerabilities, if bundled)
* Affected and fixed versions
* Mitigation guidance (hardening steps for users who cannot upgrade immediately)
* Known limitations/caveats and any breaking-change risk

In some cases, we may first ship **configuration-only mitigations** or documentation updates (tightening sample `docker-compose` defaults, recommended firewall rules, etc.) ahead of a full patch if that meaningfully reduces risk quickly.

---

## Credential and Secret Exposure

If you believe you’ve found **leaked credentials or tokens** (in this repo, release artifacts, container images, logs, or CI outputs):

* Contact us **immediately** via a private channel.
* We will **revoke or rotate** affected secrets within **24 hours of confirmation** where feasible.
* If end-users must take action (rotate their own keys, invalidate tokens), we will publish clear guidance in an advisory and/or release notes.

---

## Scope

This policy defines what is **in scope** for security reporting and support.

### In scope

* Code, configuration, and assets **in this repository**, including:

  * Core HueyOS runtime
  * Helper tools and example services (APIs, task runners, schedulers)
  * Installer scripts, configuration templates, and deployment manifests provided here
  * Example Dockerfiles, `docker-compose.yml`, and related infrastructure definitions
* Security properties of **default configurations** documented in the README/docs
* Official artifacts published under the project namespace that are documented by this repository (e.g., referenced container images)

### Out of scope (with an important caveat)

* Pure upstream vulnerabilities in:

  * Linux kernel, drivers, firmware, system libraries
  * Python runtime/stdlib
  * Third-party packages, container base images, external tools
  * Databases, message brokers, reverse proxies used alongside HueyOS
    These should generally be reported to the upstream maintainers.

**Caveat:** If an upstream issue becomes **exploitable through HueyOS defaults, integrations, or reference deployments**, report it to us as well. We can help coordinate mitigations, pinning, or upgrades on the HueyOS side while upstream fixes land.

Also out of scope:

* Attacks requiring **unreasonable physical access** for an on-robot context (e.g., direct bus probing, cold-boot lab attacks)
* Pure **social engineering**, phishing, or non-technical scams
* **Denial-of-service** issues that require unrealistic resources or have no practical remediation beyond “add capacity”
  (However, DoS vectors with realistic attacker cost and feasible mitigations *are* in scope.)
* Findings that are purely **deployment misconfigurations** outside documented recommendations
  (e.g., binding an admin API to the public internet without authentication)
* Purely **informational** findings without clear security impact (generic banners, low-value version leakage, non-sensitive debug logs in non-production)

We still appreciate reports that help clarify documentation, especially if a misconfiguration is easy to make.

---

## Safe Harbor for Good-Faith Research

We value and encourage good-faith security research on HueyOS.

As long as you:

* Comply with applicable laws
* Respect privacy and data ownership
* Do not intentionally access, modify, or exfiltrate data beyond what is necessary to demonstrate impact
* Avoid degrading availability for others (no large-scale DoS against shared environments)
* Do not retain sensitive data longer than necessary; securely delete it afterwards
* Use the private reporting channels above and allow reasonable time for remediation

…we will not initiate legal action against you solely for security research conducted in good faith on this project.

If you are unsure whether a planned test falls within these bounds, contact us first and we can provide guidance.

---

## Common Vulnerability Classes We Prioritize

Because HueyOS is an offline-first, on-robot runtime with network-reachable APIs and local governance components, we prioritize:

* **Remote code execution and injection**

  * RCE via HTTP APIs, IPC layers, task queues, configuration/serialization
  * Template/command injection, unsafe `eval`, unsafe subprocess usage
* **Privilege escalation and sandbox escape**

  * Escalation from `hueyos` user to `root`
  * Container escape where containers are documented as security boundaries
* **Authentication/authorization weaknesses**

  * Auth bypass, broken RBAC/permission checks
  * Session fixation, weak tokens, predictable identifiers
* **Path traversal and filesystem attacks**

  * Directory traversal via HTTP routes/file APIs
  * Symlink/hardlink attacks on temp files/logs/config paths
  * Unsafe default permissions for secrets/keys/sensitive logs
* **Supply-chain and artifact integrity**

  * Malicious dependencies, tampered artifacts, compromised build pipelines
  * Insecure update mechanisms (if present)
* **Information disclosure**

  * Leaks of secrets/keys/credentials (including accidental commits)
  * Sensitive logs/stack traces/config exposure via endpoints
  * Data exposure in backups/test artifacts
* **Insecure defaults and sharp edges**

  * Sensitive services bound to public interfaces by default
  * Defaults that disable encryption/integrity in easy-to-misuse ways

---

## Development and Hardening Practices

These practices guide HueyOS development and hardening. They may not be fully implemented everywhere yet, but they describe the direction of travel:

* **Least privilege by default**

  * Prefer non-root services with minimal capabilities
  * Narrow filesystem/network/kernel capabilities (systemd sandboxing, container profiles)
* **Secure defaults and documentation**

  * Secure-by-default sample configs (`huey.env.example`, `docker-compose.yml`, systemd units)
  * Document trade-offs when enabling risky/experimental features
* **Dependency hygiene**

  * Keep dependencies reasonably current, especially security-sensitive ones
  * Track upstream advisories and react in a timely fashion
* **Code review and testing**

  * Require review for security-sensitive changes
  * Add regression tests for fixed vulnerabilities where feasible
  * Use automated unit/integration tests to prevent regressions
* **Defense-in-depth**

  * Encourage containers/VMs and network segmentation
  * Consider MAC frameworks (AppArmor/SELinux) where appropriate
  * Secure temp files and IPC paths (unique dirs, safe permissions, avoid predictable names)
* **Secrets management**

  * Avoid committing secrets or baking them into images
  * Prefer env vars or secret stores with clear operator guidance
  * Document rotation and revocation procedures

---

## Example Email Report Template

```text
Subject: VULN: <short title> — impact <Critical/High/Medium/Low>

Product: Monkey-Head-Project (HueyOS)
Affected versions/commits: <e.g., 0.3.2, main @ abcdef1>
Environment: <OS/arch/kernel/deps>

Summary:
<one-paragraph description of the issue and its impact>

Reproduction:
<step-by-step or PoC snippet; HTTP requests, commands, configuration>

Impact:
<what an attacker can do; required privileges; potential data or control exposure>

Suggested fix/mitigation:
<optional, but appreciated>

Additional notes:
<logs, screenshots, or references; redact secrets>

Reporter credit:
<Name or handle; link if desired; anonymity preference>
```