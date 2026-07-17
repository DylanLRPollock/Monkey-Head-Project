# GitHub Wiki overhaul — v201.x

**Status date:** 2026-07-17  
**Release context:** Pre-Release #4  
**Source authority:** explanatory documentation; accepted plans and implementation evidence take precedence

## Purpose

The former GitHub Wiki was a 2025 snapshot. It contained useful lineage, but its active pages described retired or failed machines, obsolete kernel and Python plans, an AMD-first topology, PyGPT-net as the primary interface, and target-state governance as though those remained the current system.

The v201.x overhaul replaces that stale manual with a complete, generated, truth-layered wiki whose reviewable source lives in the main repository.

## Complete structure

The generator produces at least **66 current pages** across six domains:

1. orientation and current project position;
2. architecture, V1, PyHuey, HIMS, memory, evidence, safety, and governance;
3. hardware, Huey V4, Nexus 5/Nexus 7 controllers, repair, recovery, and LabTech;
4. development, software, models, networking, security, backups, testing, and troubleshooting;
5. contribution, style, releases, publication, licensing, privacy, risks, and human acceptance;
6. project timeline, predecessor lines, migration, historical wiki treatment, glossary, and complete page index.

It also creates:

- `_Sidebar.md` and `_Footer.md`;
- compatibility/history pages for retired 2025 URLs;
- `wiki-manifest.json` with page counts, file sizes, and SHA-256 hashes;
- `SHA256SUMS` for the generated Markdown set.

## Major corrections

| Legacy wiki claim or emphasis | v201.x treatment |
|---|---|
| iMac 5K Portal as current host | Hardware lineage or bounded LabTech role |
| BD795I-SE/ITX Core as stable compute | Historical experiment requiring revalidation |
| Kernel 6.17 and October 2025 action plan | Historical release context |
| Python 3.14 staging | Replaced by repository-declared Python 3.13 requirement |
| AMD-first architecture | Replaced by evidence-led node architecture |
| Spark/Zap two-GPU brain presented as current | Governance and architecture lineage only |
| 256 citizens and Cloud Pyramid presented operationally | Target-state doctrine, not current reality |
| PyGPT-net as primary interface | Replaced by PyHuey primary GUI/core-runtime direction |
| Distributed or federated system first | Replaced by one embodied Huey node first |
| Farm as required architecture | Re-scoped as optional supra-node infrastructure |

## Reviewable source model

GitHub stores the live wiki in the separate `Monkey-Head-Project.wiki.git` repository, which does not support ordinary pull requests. The main repository therefore owns the source and publication mechanism:

1. `scripts/repo/wiki_legacy.json` defines navigation and legacy-page disposition.
2. `scripts/repo/wiki_pages_*.json` stores reviewed detailed page specifications.
3. `scripts/repo/build_wiki.py` loads those sources, fills every remaining domain page, generates all outputs, and performs strict validation.
4. `tests/test_wiki_generator.py` verifies page counts, status blocks, sources, legacy targets, manifest content, and checksums.
5. `scripts/repo/publish_wiki.sh` publishes only the generated output.
6. `.github/workflows/publish-wiki.yml` validates pull requests, uploads the generated wiki for review, and publishes only after merge to `main` or explicit manual dispatch.

## Validation gates

The generator fails when:

- fewer than 66 current pages are defined;
- a sidebar page is missing;
- a compatibility page or its replacement target is missing;
- an internal wiki link is unresolved;
- a current page lacks the v201.x status date.

CI additionally runs the dedicated generator test module and stores the generated wiki as a workflow artifact for inspection before publication.

Successful generation validates documentation structure only. Runtime, hardware, HIMS, controller, battery, security, and Body claims still require their own implementation evidence.

## Publication credentials

The workflow first attempts the repository `GITHUB_TOKEN`. If GitHub does not permit that token to write to the separate wiki repository, configure a repository secret named `WIKI_DEPLOY_TOKEN` with permission to update the project wiki, then use manual workflow dispatch.

## Legacy source

The supplied 2025 concatenated wiki export remains the migration-audit source. Its page names and former navigation are preserved through current pages or explicit historical/compatibility treatment rather than being silently discarded or left active.
