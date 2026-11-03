# Upstream PyGPT 2.9.1 as HueyOS operator interface

This integration runs **upstream** [PyGPT](https://github.com/szczyglis-dev/py-gpt)
instead of treating the lightweight `huey.connectors.pyhuey` test stub as a
desktop application. PyGPT is MIT licensed; HueyOS retains its own GPLv3
identity. The installed PyGPT package is a separately maintained dependency,
not an embedded copy of the complete upstream source tree.

## Architecture

```text
  PyGPT 2.9.1 desktop GUI (separate Python 3.13 process)
       |
       | PyGPT MCP plugin (stdio; enabled by operator)
       v
  python -m huey.integrations.pygpt_mcp
       |
       +-- read-only project information
       +-- GET http://127.0.0.1:8000/healthz
       +-- local FFmpeg tool availability
       +-- explicit HueyOS bridge permission policy

  HueyOS API / scheduler / governance / hardware controls
       ^ unaffected; no write access delegated by this bridge
```

PyGPT's own chat, agents, Ollama, files and multimedia functionality remains
provided by upstream PyGPT, **not** reimplemented in HueyOS. This integration
provides an actual operator-to-HueyOS interface without introducing a second,
diverging PyGPT codebase. The legacy PyHuey compatibility tree remains for
older tests and adapters; it is not used by the new launcher or MCP server.

## Install (Linux, supported Python 3.13)

Use **separate virtual environments** to avoid mixing PyGPT's large GUI/ML
dependency graph with the core on-robot HueyOS environment.

```sh
# From the Monkey-Head-Project checkout:
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -e .

# Install the actual upstream GUI in its own Python 3.13 environment:
python3.13 -m venv "$HOME/.venvs/pygpt"
"$HOME/.venvs/pygpt/bin/python" -m pip install "pygpt-net==2.9.1"

# Run from the HueyOS environment; point to the GUI in the other environment:
export PYGPT_EXECUTABLE="$HOME/.venvs/pygpt/bin/pygpt"
huey-pygpt doctor
huey-pygpt gui
```

Windows: use the corresponding `Scripts\\python.exe` and
`Scripts\\pygpt.exe` paths and set `PYGPT_EXECUTABLE` in the
PowerShell session. A display server and desktop Qt dependencies are required;
the headless MCP bridge itself requires neither PySide6 nor a GPU.

If PyGPT is installed in the active environment and on `PATH`, no
`PYGPT_EXECUTABLE` override is necessary. An optional GUI profile directory
can be specified with `huey-pygpt gui --workdir /path/to/profile`.
Do not automatically point this at HueyOS's privileged data directory.

## Connect PyGPT to HueyOS

1. Start HueyOS's API on local loopback, using its existing API configuration
   and safety policy. The bridge's default health port is `8000`; set
   `HUEY_API_PORT` when using another local port.
2. In the HueyOS environment, run `huey-pygpt connector > hueyos-mcp.json`.
   This writes a standard Claude-style `mcpServers` JSON configuration using
   the exact Python executable from the environment running HueyOS.
3. In PyGPT 2.9.1, open **Config → MCP… → Connectors…**, import the JSON file,
   inspect the command and environment, and explicitly enable the connector.
4. Enable the **MCP** plugin and its exposed tools in the desired PyGPT chat or
   agent. The four commands are `huey_project`, `huey_health`,
   `huey_diagnostics` and `huey_permissions`.

PyGPT's MCP Connector manager imports configurations in common Claude/Cursor
formats, but leaves imported servers disabled until the operator enables them.

The bridge may also be started manually with `huey-pygpt mcp` or
`python -m huey.integrations.pygpt_mcp`; it exchanges newline-delimited MCP
JSON-RPC messages through **stdio**, not a network listener. Do not mix logs
or ordinary console output into stdout when running in MCP mode.

## Safety boundary

* No ability to submit Huey tasks, move servos, control power, alter
  governance, mutate memory, write files, or execute arbitrary commands.
* API health checks are restricted in code to `127.0.0.1`, `/healthz`
  and an operator-selected numeric local TCP port. No user-supplied URLs,
  HTTP redirects, or authorization credentials are accepted by this tool.
* All MCP tool names and argument schemas are allowlisted; unrecognized tools
  are rejected. The server does not load the compatibility stubs.
* These restrictions apply **only to this HueyOS connector**. PyGPT's
  *other* plugins (including Python/OS, terminal, desktop/computer use and
  custom commands) retain their own permissions; disable or sandbox them
  separately before using PyGPT near robot hardware.
* Do not enable remote hardware control or privileged robot operations as a
  shortcut. Later integrations should use separately reviewed, authenticated,
  capability-scoped APIs with explicit human approval.

## Validation

```sh
python -m pytest -q tests/test_upstream_pygpt_mcp.py
python -m huey.integrations.pygpt_cli doctor
python -m huey.integrations.pygpt_cli connector
```

These tests simulate the PyGPT GUI process, MCP messages and local health
endpoint. They **do not** replace an actual operator smoke test of upstream
PyGPT/PySide6, an Ollama model, or the real hardware. For a live smoke test,
install PyGPT, connect the MCP server, then ask PyGPT to call
`huey_health` and `huey_project`. An unavailable API must report
`connected: false`, not claim that Huey is running.
