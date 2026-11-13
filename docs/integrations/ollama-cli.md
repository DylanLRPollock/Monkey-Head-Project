# Ollama operator commands

HueyOS exposes Ollama model management and interactive inference through its main
CLI. Ollama remains an optional dependency in the `ml` profile; install the ML
extra before using these commands. The Ollama server must be running separately.

```bash
huey ollama list
huey ollama show qwen3.6:35b
huey ollama pull qwen3.6:35b
huey ollama ps
huey ollama generate qwen3.6:35b "Summarize the HueyOS project."
huey ollama chat qwen3.6:35b
```

Use `--host URL` immediately after `ollama` to target another server. If omitted,
the official client uses `OLLAMA_HOST` and then its localhost default.

The CLI also provides `push`, `create`, `copy`, and `delete`. `delete` asks you to
type the exact model name unless `--yes` is supplied. `push` uploads the selected
model to its registry namespace; confirm its name and destination before running it.

```bash
huey ollama create huey-assistant --from qwen3.6:35b --system "You are Huey."
huey ollama copy qwen3.6:35b huey-backup:latest
huey ollama delete huey-backup:latest
```
