# Security Policy

The Monkey-Head-Project (**HueyOS**) takes security seriously. This policy explains what we support, how to report issues, and how we coordinate fixes, backports, and disclosure across the project’s on-robot runtime, helper tools, and reference deployments.

HueyOS is typically deployed as an **offline-first**, self-hosted system with tightly scoped network surfaces. Even so, we treat every externally reachable interface (HTTP APIs, admin consoles, message queues, etc.) as potentially hostile and design our security posture accordingly.

---

## Supported Versions

We use semantic versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR:** Structural or incompatible changes to APIs, storage, or governance assumptions.
- **MINOR:** Backward-compatible feature releases and roadmap milestones.
- **PATCH:** Bugfix and security releases only.

Security support normally covers **the current minor** and **the previous minor** lines. Older versions are unsupported unless explicitly noted in a security advisory (for example, if a widely used but older line requires a one-off fix).

> The table below is illustrative and is updated when new releases are cut and tagged.

| Version / Line            | Status                                   |
|---------------------------|------------------------------------------|
| `0.3.x` (current)         | ✅ Actively supported                    |
| `0.2.x` (previous)        | 🔶 Critical fixes only                   |
| `< 0.2.0`                 | ❌ Unsupported                           |
| `main` (default branch)   | ✅ Fixes land here before release        |

**Additional notes**

- Security fixes generally first land on `main`, then are **backported** to supported minors as appropriate.
- Development branches and feature branches are **not** covered by this policy; they may contain experimental or partially hardened code.
- Distributors or downstream forks built on top of HueyOS should clearly document which upstream version/commit they track and apply their own support window.

### Supported Platforms (runtime)

HueyOS is designed and tested primarily against the following environment:

- **OS:**  
  - Debian 13 “Trixie” (stable) — **primary supported** platform.  
  - Debian 14 “Forky” — **staging/preview** only until explicitly promoted in release notes.
- **Arch:**  
  - `amd64` (x86_64). Other architectures (ARM, RISC-V, etc.) may work but are currently out of scope for security guarantees.
- **Kernel:**  
  - HueyOS tracks Linux LTS or near-LTS kernels with project-specific configuration (e.g., `6.x-huey*`).  
  - The exact supported kernel series for each release are documented in the corresponding release notes and changelog.

**Virtualization and containers**

- Running HueyOS inside containers (Docker, Podman, etc.) or virtual machines (KVM, VirtualBox, etc.) is supported **as long as** the underlying host matches the OS/arch/kernel assumptions above.
- Container images and `docker-compose` files provided in this repository are considered **in scope**. Host misconfiguration outside documented recommendations is not.

---

## Reporting a Vulnerability

We strongly prefer **coordinated vulnerability disclosure**. Please use a **private channel** and provide enough information for us to reproduce the issue and understand its impact.

### Private Channels

1. **GitHub – Private Vulnerability Report (preferred)**  
   - Navigate to the repository → **Security** tab → **Report a vulnerability**.  
   - This path automatically records the report, keeps details private, and helps us track fixes and advisories.

2. **Email**  
   - Address: **admin@dlrp.ca**  
   - Subject line: `VULN: <short title>`  
   - If you require encryption, indicate this in your first email (e.g., “Please send your PGP key”). We will reply with a public key and instructions.

If you are unsure whether something qualifies as a vulnerability, err on the side of reporting it privately; we can help classify it.

### What to Include

The more detail you can safely provide, the faster and more accurately we can triage:

- A clear **summary of the issue** and its **security impact** (e.g., “unauthenticated RCE via …”).
- **Reproduction steps / PoC**, including:
  - Exact commands, HTTP requests, or payloads used.
  - Relevant configuration (e.g., `huey.env`, `docker-compose.yml`, or systemd units), with secrets redacted.
  - Any necessary environment prerequisites (e.g., specific hardware, optional modules).
- **Affected versions/commits and environment**:
  - HueyOS version(s), Git commit hash, or branch.
  - OS (e.g., Debian 13), architecture, kernel version.
  - Any non-default dependencies, kernels, or external services in play.
- Any **mitigations or workarounds** you’ve identified, even if partial.
- Preferred **credit** (name/handle, link) or an explicit note if you prefer anonymity.

Please avoid opening public GitHub issues or pull requests that contain exploit details, stack traces with sensitive context, or configuration dumps until we have agreed on a disclosure timeline.

---

## Triage & Service Levels (Targets)

We use CVSS v3.1 as a starting point for severity, combined with contextual factors (deployment mode, default configuration, reachable surfaces in typical HueyOS setups).

**Target timelines (best-effort):**

- **Acknowledgement:** within **72 hours** of receiving your report.
- **Initial triage & severity assessment:** within **7 calendar days**.
- **Fix/mitigation targets** (from acknowledgement):
  - **Critical (CVSS ≥ 9.0):**  
    Aim for a fix or robust mitigation within **14–21 days**.
  - **High (7.0–8.9):**  
    Aim for mitigation and/or patch within **21–30 days**.
  - **Medium (4.0–6.9):**  
    Aim for a fix or recommended mitigation within **30–60 days**.
  - **Low (< 4.0):**  
    Scheduled based on impact, complexity, and available capacity.

These are **targets**, not guarantees. Complex issues, upstream dependencies, or hardware-specific problems may require more time; conversely, actively exploited issues may be resolved faster.

### Triage Process

During triage, we usually:

1. **Reproduce** the issue in a controlled environment, mirroring the reporter’s configuration where possible.
2. **Confirm impact and scope**, including:
   - Required privileges or preconditions.
   - Potential for lateral movement or data exfiltration.
   - Applicability to typical HueyOS deployments (on-robot vs. lab vs. test rigs).
3. **Assign provisional severity** based on CVSS v3.1 and contextual risk.
4. **Identify affected versions** and any relevant derivatives (e.g., example Docker deployments).
5. **Plan remediation**, including:
   - Short-term mitigations (configuration or ACL changes).
   - Long-term patches, architectural changes, or documentation updates.
6. **Communicate** initial findings and planned next steps to the reporter.

We provide **weekly status updates** to reporters while an issue remains open, or more frequently if there are important milestones or changes.

### Severity Reference

| Severity  | CVSS (v3.1) |
|-----------|-------------|
| Critical  | 9.0–10.0    |
| High      | 7.0–8.9     |
| Medium    | 4.0–6.9     |
| Low       | 0.1–3.9     |

If your assessment suggests a different severity than ours (e.g., due to deployment realities we may have missed), you are welcome to share your reasoning and we will re-evaluate.

---

## Coordinated Disclosure & Embargo

Our default stance is that security issues should be disclosed responsibly and with sufficient time for users to patch.

- **Default embargo window:** **90 days** from acknowledgement of the report.
- We may **shorten the embargo** if:
  - There is credible evidence of active exploitation in the wild.
  - The vulnerability is trivially exploitable and widely exposed by default.
  - A fix or strong mitigation is available and simple to deploy.
- We may **extend the embargo** by mutual agreement if:
  - The issue is complex and requires substantial architectural change.
  - There are dependencies on upstream fixes or coordination with other projects.

**Advisory publication**

- Advisories are published via **GitHub Security Advisories** for this repository.
- We request a **CVE ID** for qualifying issues and reference it in release notes, documentation, and the advisory itself.
- Credits are included with the reporter’s permission. Anonymous or pseudonymous credit is fully supported.

If you intend to publish your own write-up, we ask that you coordinate timing with us so that users have access to patches or mitigations when details become public.

---

## Fix, Backport, and Release Policy

When a vulnerability is confirmed:

1. **Patches are developed and reviewed** on a private or restricted branch when appropriate.
2. Once ready, patches are merged into `main` and, where feasible:
   - **Backported** to all actively supported minor lines.
   - Evaluated for backporting to older lines if they are widely deployed and the risk is high.
3. A **security release** is cut for each affected maintained line:
   - Security releases increment the `PATCH` component (e.g., `0.3.4` → `0.3.5`).
   - Release notes clearly indicate that the version includes security fixes.

Each security release will include:

- A summary of the vulnerability (or multiple vulnerabilities, if bundled).
- Affected and fixed versions.
- Mitigation or configuration guidance (including hardening steps for users who cannot upgrade immediately).
- Any known limitations, caveats, or breaking-change risk.

In some cases, we may first ship **configuration-only mitigations** or documentation updates (for example, tightening sample `docker-compose` files or recommended firewall rules) ahead of a full patch when that meaningfully reduces risk quickly.

---

## Scope

This policy defines what is considered **in scope** for security reporting and support.

**In scope**

- Code, configuration, and assets **in this repository**, including:
  - Core HueyOS runtime.
  - Example services (APIs, task runners, schedulers).
  - Installer scripts, configuration templates, and deployment manifests provided here.
  - Example Dockerfiles, `docker-compose.yml`, and related infrastructure definitions.
- Security properties of **default configurations** documented in this project’s README and docs.
- Official artifacts published under the project namespace (e.g., container images documented in the repo).

**Out of scope**

- Vulnerabilities in **upstream dependencies**, including:
  - Linux kernel, drivers, firmware, system libraries.
  - Python runtime and standard library.
  - Third-party Python packages, container base images, and external tools.
  - Databases, message brokers, or reverse proxies used alongside HueyOS.
  - These should be reported to their respective maintainers. If you are unsure, we can help route reports.
- Issues that **require physical access** beyond what is reasonable to protect against in an on-robot context (e.g., direct bus probing, cold-boot attacks against lab hardware).
- Pure **social engineering** attacks, phishing, or non-technical scams.
- **Denial-of-service** issues that require unrealistic resource levels, or that have no practical remediation beyond “increase capacity” or “rate limit harder.”
- Findings that are **deployment misconfigurations** outside our documented recommendations (e.g., binding an admin API directly to the public internet without authentication).
- **Informational findings** without a clear security impact, such as:
  - Generic banner disclosures.
  - Version leaks without a plausible exploitation path.
  - Non-sensitive debug logs in non-production environments.

That said, we still appreciate reports that help clarify or improve documentation, especially if a particular misconfiguration is likely or easy to make.

---

## Safe Harbor for Good-Faith Research

We value and encourage good-faith security research on HueyOS and related components.

As long as you:

- Comply with all applicable laws.
- Respect the **privacy and data ownership** of others.
- Do not intentionally access, modify, or exfiltrate data beyond what is strictly necessary to demonstrate impact.
- Avoid degrading availability for other users (no large-scale DoS tests against multi-tenant services).
- Do not retain sensitive data discovered during testing beyond what’s necessary to craft a report, and securely delete it afterwards.
- Use the **private reporting channels** described above and allow reasonable time for remediation.

…we will **not initiate legal action** against you solely for your security research on this project.

If you are unsure whether a planned test falls within these bounds, contact us first and we can provide guidance.

---

## Common Vulnerability Classes We Prioritize

Because HueyOS is an offline-first, on-robot runtime with network-reachable APIs and local governance components, we prioritize the following classes of issues:

- **Remote code execution and injection**
  - Arbitrary code execution via HTTP APIs, IPC layers, task queues, or configuration deserialization.
  - Template injection, command injection, or unsafe use of `eval`/subprocess calls.

- **Privilege escalation and sandbox escape**
  - Gaining higher OS privileges (e.g., from `hueyos` user to `root`).
  - Escaping containers or restricted environments that are documented as security boundaries.

- **Authentication / authorization weaknesses**
  - Bypass or subversion of authentication flows for admin consoles or APIs.
  - Broken role-based access control (RBAC) or permission checks.
  - Session fixation, weak tokens, or predictable identifiers.

- **Path traversal and filesystem attacks**
  - Directory traversal via HTTP routes or file APIs.
  - Symlink or hardlink attacks against temporary files, log files, or configuration paths.
  - Unsafe default file permissions for secrets, keys, or sensitive logs.

- **Supply-chain and artifact integrity**
  - Malicious dependencies, tampered distribution artifacts, or compromised build pipelines.
  - Insecure update mechanisms, if any, that could be abused to deliver malicious code.

- **Information disclosure**
  - Leaks of secrets, keys, or credentials (including those accidentally committed).
  - Exposure of sensitive logs, stack traces, or configuration files via web endpoints or misconfigured file servers.
  - Inadvertent data exposure in backups or test artifacts.

- **Insecure defaults and misconfigurable surfaces**
  - Defaults that bind sensitive services to public interfaces without authentication.
  - Defaults that disable encryption or integrity checks in ways that are easy to misuse.

If you believe you’ve found **leaked credentials or tokens** (whether in this repo, attached artifacts, or public logs):

- Contact us **immediately** via a private channel.
- We will **revoke or rotate** affected secrets within **24 hours of confirmation**.
- If end-users must take action (e.g., rotate their own keys), we will publish guidance in an advisory or release note.

---

## Development & Hardening Practices (Policy Direction)

The following practices guide how we develop and harden HueyOS. They may not be fully implemented everywhere yet, but they describe the direction of travel:

- **Least privilege by default**
  - Prefer running services as non-root users with minimal capabilities.
  - Narrow filesystem, network, and kernel capabilities where possible (e.g., via systemd unit restrictions or container profiles).

- **Secure configuration and documentation**
  - Provide secure-by-default sample configs (`huey.env.example`, `docker-compose.yml`, systemd units).
  - Clearly document any trade-offs when enabling risky or experimental features.

- **Dependency hygiene**
  - Keep dependencies as current as is practical, especially those with known security histories (web frameworks, cryptography, serialization, etc.).
  - Review security advisories from upstream projects and react in a timely fashion.

- **Code review and testing**
  - Require review for security-sensitive changes.
  - Add regression tests for fixed vulnerabilities where feasible, to prevent re-introduction.
  - Use automated test suites (unit, integration) to catch common failure modes.

- **Defense-in-depth**
  - Encourage isolation boundaries: containers, VMs, and network segmentation.
  - Consider use of MAC frameworks (e.g., AppArmor, SELinux) and sandboxing primitives where appropriate.
  - Handle temp files and IPC paths in secure ways (unique directories, safe permissions, avoiding predictable names).

- **Secrets management**
  - Avoid storing secrets in the repository or baked into images.
  - Prefer environment variables or dedicated secret stores, with clear documentation for operators.
  - Provide guidance for rotating keys and revoking access.

These practices inform how we evaluate patches and designs. In some sub-components, implementation may lag behind the ideal; in others, the controls may be stricter.

---

## Communication Cadence with Reporters

For each valid security report, we aim to:

- **Acknowledge** receipt within **72 hours**.
- Provide an **initial triage outcome and severity** within **7 days**.
- Send **weekly updates** while the issue remains open or until it transitions to a released advisory.
- Before publication, share:
  - Planned disclosure and release timelines.
  - High-level remediation notes and any recommended administrator actions.
- After release, send:
  - A link to the published advisory.
  - Final affected/fixed version lists.
  - Credit details (if you requested attribution).

If you ever feel communication has stalled, a polite ping on the original channel is welcome.

---

## Example Email Report Template

You can use the template below when reporting via email:

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
