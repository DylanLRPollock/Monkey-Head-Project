# PyGPT Vendor Mirrors

This directory holds lightweight PyGPT/PyGPT-net mirrors used by HueyOS tests
and constrained developer environments.

The active runtime integration is resolved by `huey.pyhuey_integration` in this
order:

1. the packaged connector tree under `src/huey/connectors/pyhuey`,
2. the full `integrations/pyhuey` submodule,
3. these vendored mirrors,
4. legacy checkout locations.

Legacy imports through `huey.pygpt_net` remain supported as a compatibility shim
that points at the packaged connector tree.

Keep live adapter and submodule work under `integrations/`; keep static mirrors
here under `vendor/`.
