# Memory subsystem consolidation, Stage 2

## Responsibilities

- Source: src/huey/memory/{ingestion,indexing,metadata,preload_data}.py.
- User data: configured MEMORY_PATH (or existing project memory path).
- Legacy huey.memory.PY.* remains as compatibility import aliases,
  retaining the same module object for mocks, importers and patching.
- Command Center uses canonical huey.memory.indexing and read-only status
  inspection must not create directories.

## Safety

1. Different source files with the same name cannot silently replace stored
   copies. Identical copies are reused; different bytes raise FileExistsError.
2. JSON ingestion validates syntax before storing.
3. Media summary reads the structured probe result, not its raw JSON mapping.
4. Index persistence uses a same-directory temporary file and os.replace;
   failure retains the earlier index.
5. Discovery skips hidden files, symlinks, executable code folder PY, cache
   folders and generated INDEX data. Results have deterministic sorted order.
6. scripts/memory_index.py defaults to dry run and requires --root; saving
   requires explicit --write --index-path. Dry run reads no file contents.
7. Preload selects a bundled prompt CSV and excludes executable source.

## Validation and limitations

Run: python -m pytest tests/test_memory_migration.py -q

Dry-run example:

    python scripts/memory_index.py --root /path/to/memory --json

Explicit write example:

    python scripts/memory_index.py --root /path/to/memory --index-path /path/to/memory/INDEX/memory-index.json --write --json

This does not replace Honeycomb, add vector search or enable privileged
actions. There is no automatic background indexing. PDF text requires
pypdf and media metadata requires FFmpeg. Before indexing private data,
the operator must decide retention and access policies.

Follow-up: migrate remaining consumers, test larger/corrupt data, bound index
sizes, add versioned schemas and move mutable state outside bundled sources.
