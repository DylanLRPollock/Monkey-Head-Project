# V1 fixture integrity and proof-loop compatibility

This stage strengthens the existing canonical `huey.v1` implementation rather
than moving a second proof-loop implementation into the maintained package.

## Changes

- `register_fixture` refuses duplicate fixture IDs by default. Explicit
  `overwrite=True` is required to replace an ID.
- `copy_to_registry` reuses identical existing files and refuses a destination
  with a different checksum instead of silently overwriting it.
- The canonical registry is written through a temporary file and `os.replace`.
- `load_fixture` verifies SHA-256 and size by default; `verify=False` is
  available for inspection of corrupt legacy records, not for runtime execution.
- `run_fixture` validates integrity when called with a registered fixture
  record that includes metadata; explicit bare paths remain user-authorized.
- Old `huey.memory.PY` proof-loop, response-bridge and JSONL log modules
  now resolve to the same canonical module objects, preserving import identity.
- The V1 API response mode now fails when configured but unimplemented. It
  no longer pretends to have generated a remote response.
- HTML reports escape untrusted user transcript, response, and run-ID values.
- Structured run logs reject JSONL entries that are not objects.

## Scope limits

The legacy `huey.memory.PY.fixture_registry` also contains a distinct
`FixtureRegistry` class with a different on-disk schema. It is deliberately
left untouched here, pending a dedicated schema/compatibility migration.
The canonical functional registry keeps its existing flat JSON record format.

This does not introduce hardware control, automatic LLM execution, or
automatic background proof runs. It does not guarantee cross-process
transactional locking; multiwriter support needs its own change.

## Validation

Run:

    python -m pytest tests/test_v1_fixture_integrity.py -q

Full Python 3.13 CI, lint, package smoke and security scanning remain required.
The repository-wide 80% coverage gate is unchanged.
