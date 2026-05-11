# PyHuey / PyGPT vendor placeholder

This directory emulates the upstream [`py-gpt`](https://github.com/szczyglis-dev/py-gpt) submodule used by Monkey Head. It contains a lightweight `pygpt_net` compatibility stub used during the PyHuey cockpit identity migration, so the project can run and test without fetching the full upstream repository.

## Compatibility and identity notes

- Upstream package identity and compatibility are preserved via the `pygpt-net` project name and `pygpt` console script.
- A `pyhuey` console script is also exposed, mapped to the same entrypoint as `pygpt`.
- This stub preserves PyGPT provenance; it is not presented as a separate published `pyhuey` package.

If you need the full implementation, replace this directory with the real submodule checkout or install `pygpt-net` from PyPI.
