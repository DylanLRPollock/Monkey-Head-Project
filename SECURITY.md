# Security Policy

The Monkey‑Head‑Project (**HueyOS**) takes security seriously. This policy explains what we support, how to report issues, and how we coordinate fixes and disclosure.

---

## Supported Versions

We use semantic versioning (`MAJOR.MINOR.PATCH`). Security support covers **the current minor** and **the previous minor** lines. Older versions are unsupported unless otherwise stated in an advisory.

> Table updates when new releases are cut.

| Version / Line            | Status                         |
|---------------------------|--------------------------------|
| `0.3.x` (current)         | ✅ Actively supported           |
| `0.2.x` (previous)        | 🔶 Critical fixes only          |
| `< 0.2.0`                 | ❌ Unsupported                  |
| `main` (default branch)   | ✅ Fixes land here before release |

### Supported Platforms (runtime)
- **OS:** Debian 13 “Trixie” (stable). Debian 14 “Forky” builds are **staging/preview** only.
- **Arch:** `amd64` (x86_64). Other architectures are currently out of scope.
- **Kernel:** HueyOS tracks Linux LTS or near‑LTS kernels; see release notes for exact versions.

---

## Reporting a Vulnerability

We prefer **coordinated vulnerability disclosure**. Use a **private channel** and provide enough detail for reproduction.

### Private Channels
1. **GitHub – Private Vulnerability Report (preferred):** Repo → **Security** tab → **Report a vulnerability**.  
2. **Email:** **admin@dlrp.ca** (subject: `VULN: <short title>`). If you require encryption, request our PGP key in your first email and we will provide it.

### What to Include
- Clear description of the issue and **security impact**.
- **Reproduction steps / PoC**, incl. configs, payloads, or minimal programs.
- **Affected versions/commits**, environment (OS, arch, dependencies, kernel).
- Any **mitigations or workarounds** you’ve identified.
- Preferred **credit** name/handle (or state you prefer anonymity).

Please avoid opening public issues/PRs that expose details before coordination.

---

## Triage & Service Levels (Targets)

We follow CVSS v3.1 for initial severity. Targets are best‑effort and may compress/expand depending on complexity and scope.

- **Acknowledgement:** within **72 hours**.
- **Initial triage & severity:** within **7 days**.
- **Fix/mitigation targets:**
  - **Critical (CVSS ≥ 9.0):** fix or viable mitigation within **14–21 days**.
  - **High (7.0–8.9):** within **21–30 days**.
  - **Medium (4.0–6.9):** within **30–60 days**.
  - **Low (< 4.0):** scheduled as capacity allows.

We provide **weekly status updates** to reporters while an issue is open. Fixes are backported to supported lines where feasible.

### Severity Reference
| Severity  | CVSS (v3.1) |
|-----------|-------------|
| Critical  | 9.0–10.0    |
| High      | 7.0–8.9     |
| Medium    | 4.0–6.9     |
| Low       | 0.1–3.9     |

---

## Coordinated Disclosure & Embargo

- Default **embargo window:** **90 days** from acknowledgement. We can adjust by mutual agreement.
- If active exploitation is observed, we may **expedite advisories** and publish interim mitigations.
- We publish advisories via **GitHub Security Advisories** and request a **CVE** when appropriate.
- Credits are included with permission. Anonymous credit is respected.

---

## Fix, Backport, and Release Policy

- Patches land on `main`, then are **backported** to supported minors when practical.
- Security releases bump **PATCH** (e.g., `0.3.4`) and include:
  - Summary of the issue and impact
  - Affected versions and fixed versions
  - Mitigation guidance and any breaking‑change notes
- We may ship **configuration‑only mitigations** ahead of a full patch when this reduces risk quickly.

---

## Scope

**In scope**
- Code and assets in this repository (HueyOS / Monkey‑Head‑Project).
- Installer scripts, configuration templates, and example manifests included here.

**Out of scope**
- Vulnerabilities in **upstream dependencies** (e.g., kernel, drivers, firmware, distro packages). Please report those to their maintainers. We will help route reports when feasible.
- Issues requiring **physical access**, **social engineering**, or attacks on external services we don’t control.
- **DoS** requiring unrealistic resource levels or without actionable remediation.
- Findings that are **misconfigurations** outside of our documented recommendations.
- **Informational** reports without a demonstrated security impact.

---

## Safe Harbor for Good‑Faith Research

We welcome research performed within these bounds:
- Do not access, modify, or exfiltrate data beyond what’s necessary to demonstrate impact.
- Don’t degrade service availability for others.
- Don’t retain sensitive data discovered during testing.
- Give us reasonable time to remediate before public disclosure.

We will not pursue legal action for research that abides by this policy and applicable laws.

---

## Common Vulnerability Classes We Prioritize

- **Remote code execution, code injection, and deserialization risks**
- **Privilege escalation** and sandbox/container breakout
- **Authentication/authorization bypass**; weak session handling
- **Path traversal, symlink/hardlink attacks, unsafe file permissions**
- **Supply‑chain issues** (malicious dependencies, tampered artifacts)
- **Information disclosure** (including secrets accidentally committed)
- **Unsafe default configurations** leading to exposure

If you believe you’ve found leaked credentials or tokens, contact us immediately; we will **revoke/rotate within 24 hours** of confirmation and follow with a public note if end‑users must act.

---

## Development & Hardening Practices (Policy Direction)

- Prefer **least privilege** defaults; document secure configuration.
- Keep dependencies current; evaluate security advisories before upgrades.
- Require **code review** for security‑sensitive changes.
- Add regression tests for fixed vulnerabilities where practical.
- Consider **defense‑in‑depth**: sandboxing, seccomp/AppArmor, and safe temp‑file handling.
- Avoid storing secrets in the repository; use environment variables or secure stores.

These are policy goals; enforcement levels may vary by sub‑component and maturity.

---

## Communication Cadence with Reporters

- We’ll send weekly updates while an issue is open (or sooner if milestones change).
- Before publication, we’ll share planned timelines and remediation notes.
- After release, we’ll send the advisory link and credit details (if applicable).

---

## Example Email Report Template

```
Subject: VULN: <short title> — impact <High/Med/Low>

Product: Monkey‑Head‑Project (HueyOS)
Affected versions/commits: <e.g., 0.3.2, main @ abcdef1>
Environment: <OS/arch/deps>

Summary:
<one-paragraph description of the issue and its impact>

Reproduction:
<step-by-step or PoC snippet; commands/config>

Impact:
<what an attacker can do; required privileges; scope>

Suggested fix/mitigation:
<optional>

Reporter credit:
<Name or handle; link if desired; anonymity preference>
```

---

## Policy Changes

This policy may evolve. Material changes will be committed to the repository and noted in the changelog.

_Last updated: 2025‑10‑25_
