# GitHub Wiki overhaul — v201.x

**Status date:** 2026-07-17  
**Release context:** Pre-Release #4  
**Source authority:** explanatory documentation; accepted plans and implementation evidence take precedence

## Purpose

The existing GitHub Wiki was a 2025 snapshot. It contained useful lineage, but its active pages still described retired or failed machines, obsolete kernel and Python plans, an AMD-first topology, PyGPT-net as the primary interface, and target-state governance as though those remained the current system.

The v201.x overhaul replaces that broad but stale manual with a smaller, truth-layered wiki generated from `scripts/repo/build_wiki.py`.

## New structure

The generated wiki contains current pages for:

- project position and identity boundaries;
- evidence-backed current status;
- node-first architecture;
- Huey V4 physical direction;
- HueyNexusController and all supported Nexus 5/Nexus 7 variants;
- PyHuey, runtime, and the V1 fixture-to-log proof;
- HIMS transport and authority boundaries;
- current hardware and LabTech distinctions;
- truth classes and documentation authority;
- governance status and human oversight;
- development, validation, roadmap, repository map, migration map, and glossary.

It also generates `_Sidebar.md`, `_Footer.md`, and concise historical notices for 33 old wiki page names so existing links do not silently continue presenting stale instructions.

## Major corrections

| Legacy wiki claim or emphasis | v201.x treatment |
|---|---|
| iMac 5K Portal as current host | Retired/decommissioned lineage |
| BD795I-SE/ITX Core as stable compute | Failed/non-posting lineage |
| Kernel 6.17 and October 2025 action plan | Historical release context |
| Python 3.14 staging | Replaced by repository-declared Python 3.13 requirement |
| AMD-first architecture | Replaced by evidence-led, hardware-neutral node architecture |
| Spark/Zap two-GPU brain presented as current | Governance and architecture lineage only |
| 256 citizens and Cloud Pyramid presented operationally | Target-state doctrine, not current reality |
| PyGPT-net as primary interface | Replaced by PyHuey primary GUI/core-runtime direction |
| Distributed or federated system first | Replaced by one embodied Huey node first |
| Farm as required architecture | Re-scoped as optional supra-node infrastructure |

## Publication model

GitHub stores a repository wiki in a separate `Monkey-Head-Project.wiki.git` repository. That repository does not support ordinary pull requests.

The main repository therefore owns the reviewable source and publication mechanism:

1. `scripts/repo/build_wiki.py` generates and validates all wiki pages.
2. `scripts/repo/publish_wiki.sh` synchronizes the generated pages to the wiki repository.
3. `.github/workflows/publish-wiki.yml` runs the process after relevant changes reach `main`, or by manual dispatch.

The workflow first attempts the repository `GITHUB_TOKEN`. If GitHub does not permit that token to write to the separate wiki repository, add a repository secret named `WIKI_DEPLOY_TOKEN` with repository wiki write access.

## Validation boundary

The generator checks that internal wiki links and legacy redirect targets resolve and that every current content page contains the v201.x status date. Runtime, hardware, and controller claims remain subject to their own tests and evidence; successful wiki generation does not validate those systems.

## Legacy source

The supplied 2025 concatenated wiki export remains the source used for the migration audit. It identifies the former page names, navigation structure, and stale claims that the redirect map and migration page explicitly address.
