# Disposition of the 144 legacy Python files

Source: the supplied python_unsorted.zip (144 Python files), compared with
src/huey/memory/PY at the base commit recorded in
legacy-python-144-disposition.json.

## What this changes

- Relocates seven previously uncollected tests to tests/, the configured
  pytest testpaths.
- Relocates nine opt-in demos to examples/. They are never started
  automatically.
- Deletes those sixteen original files from the legacy directory.
- Provides a file-by-file owner, candidate destination, source blob SHA
  and disposition for all 144 originally supplied files.
- Adds CI tests detecting unaccounted additions, removals or missing targets.

The legacy directory should contain 128 Python files after this patch.
Eleven of those are established compatibility aliases. The other 117
are not automatically unused or ready for deletion.

## Runtime constraints

huey.__getattr__, huey.os.__path__ and scripts/automation/py/_dispatch.py
can all resolve legacy modules dynamically. API, CLI and GUI also
import legacy implementations or delegate to them. Zero static imports
is not evidence of zero runtime users. A same-named file can itself be
just a wrapper rather than an equivalent maintained implementation.

The disposition implementation_parity_review does not establish behavior
equivalence. safety_review_before_promotion covers powerful filesystem,
platform, container and network operations that must not be exposed to
agents without explicit capability and operator authorization.
legacy_test_pending_parity means tests have stale or unverified APIs.

## Remaining gates

1. Resolve API and privileged subprocess boundaries first (security PR
   #851 and issue #852).
2. Preserve the historical FixtureRegistry schema under a named V1
   compatibility owner, then plan an explicit migration for its data.
3. Integrate API/CLI/GUI entrypoints one at a time with import parity tests.
4. Reconcile media/Honeycomb maintained code versus auto-generated shims.
5. Move maintenance/platform tools behind safe dry-run CLI entrypoints.
6. Retire the dynamic dispatcher only after consumers have real entrypoints.
7. Run Python 3.13 tests, 3.14 experimental checks, Bandit, CodeQL,
   and repository lint before each additional deletion.

This is an inventory plus the first physical relocation, not a declaration
that the remaining 128 legacy modules have been fully integrated.
