# PyGPT Vendor Mirrors

This directory holds lightweight PyGPT/PyGPT-net mirrors used by HueyOS tests
and constrained developer environments.

The active runtime integration is resolved by `huey.pyhuey_integration` in this
order:

1. the packaged compatibility tree under `src/huey/pygpt_net`,
2. the full `integrations/pyhuey` submodule,
3. these vendored mirrors,
4. legacy checkout locations.

Keep live adapter and submodule work under `integrations/`; keep static mirrors
here under `vendor/`.
