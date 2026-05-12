# Provenance and Licenses (Monkey-Head-Project / PyHuey Boundary)

This document records the current, repository-visible licensing and provenance boundaries for Monkey-Head-Project and the PyHuey integration surface.

## 1) Monkey-Head-Project code license

- Repository root `LICENSE` contains the GNU GPL v3 text.
- `pyproject.toml` declares the package license as `GPL-3.0-only`.
- `README.md` license section also states code is `GPL-3.0-only`.

**Current interpretation:** project code in this repository is GPLv3-only unless a file or subcomponent explicitly states otherwise.

## 2) Documentation/media license (as currently stated)

- `README.md` states: documentation and media are licensed under `CC-BY-SA-4.0` unless otherwise noted.
- README badges also display:
  - code license: GPLv3
  - docs/media license: CC-BY-SA-4.0

**Current interpretation:** docs/media follow CC-BY-SA-4.0 by default where no override is provided.

## 3) PyHuey fork basis and integration boundary

PyHuey is tracked as an integration boundary, not as the Huey Brain runtime core:

- `.gitmodules` defines `integrations/pyhuey` as a Git submodule from `https://github.com/DylanLRPollock/PyHuey.git`.
- `vendor/pygpt/README.md` states runtime integration order that includes `integrations/pyhuey` and identifies `vendor/pygpt` as static mirrors.
- `infra/docker/pyhuey/README.md` states the PyHuey image is optional cockpit/tooling and separate from the main HueyOS runtime image.

**Boundary rule in practice:** treat `integrations/pyhuey` (and associated vendor mirrors) as a provenance-preserving third-party/fork-derived integration surface, not as a silently absorbed part of Huey Brain V1 runtime claims.

## 4) Upstream PyGPT provenance

Repository docs already describe PyHuey as derived from upstream PyGPT/PyGPT-net:

- `infra/docker/pyhuey/README.md` explicitly says the cockpit image is derived from upstream `pygpt-net` for provenance/compatibility.
- `vendor/pygpt/README.md` labels the vendored content as PyGPT/PyGPT-net mirrors.

At the time of writing, the local checkout does not expose a populated `integrations/pyhuey` tree with a visible upstream license file in this repository snapshot. For license-accurate redistribution of that integration, ensure the initialized submodule retains upstream license and attribution files.

## 5) Rule for copying code across boundaries

To avoid mixing legal obligations silently:

1. **Do not copy code** between Monkey-Head-Project core paths and PyHuey/PyGPT-derived paths without preserving original copyright and license notices.
2. **When importing/adapting upstream snippets**, add provenance comments or commit notes that identify source repository and commit/tag.
3. **Keep integration paths explicit** (`integrations/pyhuey`, `vendor/pygpt`) so reviewers can distinguish first-party code from fork/vendor code.
4. **If license terms differ or are uncertain**, stop and verify upstream license files before merging copied code.

This policy is procedural/documentary only; it does not change any license terms.

## 6) NOTICE expectations

There is no repository-wide `NOTICE` file requirement explicitly declared in current top-level license metadata. However, if a copied or bundled third-party component requires NOTICE preservation, include that NOTICE text in the distributed artifact or in a dedicated notices file for that component.

Recommended minimal practice for this repository:

- Keep upstream LICENSE/NOTICE files in submodules/vendors when present.
- Record provenance in docs or release notes when syncing/updating fork/vendor content.
- Do not remove upstream attribution headers from imported files.

## 7) Non-goals / explicit limits

- This document does **not** relicense any component.
- This document does **not** claim legal terms not present in current repository files.
- This document is a provenance boundary guide for contributors and maintainers.
