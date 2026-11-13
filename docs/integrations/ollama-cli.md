# Ollama operator commands

HueyOS exposes Ollama model management and local inference through `huey ollama`.
The Python client is optional and is included in the existing `ml` profile. The
Ollama server must be running separately. Set `OLLAMA_HOST` or pass `--host URL`
immediately after `ollama` to select a server.

## Model management

```bash
huey ollama list
huey ollama show qwen3.6:35b
huey ollama pull qwen3.6:35b
huey ollama ps
huey ollama stop qwen3.6:35b
huey ollama stop --all
huey ollama copy qwen3.6:35b huey-backup:latest
huey ollama delete huey-backup:latest
```

Deletion asks you to type the exact model name unless `--yes` is supplied. `stop`
only unloads a model from memory; it does not delete the model.

Create a model from inline options or an existing Modelfile:

```bash
huey ollama create huey-assistant --from qwen3.6:35b \
  --system "You are Huey." --param num_ctx=8192 --param temperature=0.7
huey ollama create huey-custom --modelfile ./Modelfile
```

Inline creation uses the Python client. Modelfile creation invokes the installed
`ollama create` command so Ollama parses the full file format. When targeting a
remote server, the command passes the selected host through `OLLAMA_HOST`.

## Generation and chat

```bash
huey ollama generate qwen3.6:35b "Summarize the HueyOS project." --preset qwen-8k
huey ollama generate qwen3.6:35b "Return a JSON summary." --format-json
huey ollama chat qwen3.6:35b --preset qwen-8k --system "You are Huey."
huey ollama chat llava --image ./diagram.png
huey ollama chat qwen3.6:35b --tools
```

The `qwen-8k` preset sets an 8192-token context window. `deterministic` provides
low-variance generation settings. Per-command flags such as `--num-ctx`,
`--num-predict`, `--temperature`, `--top-p`, and `--top-k` override preset values.
Use `--format-schema schema.json` to request a JSON-schema-constrained response.
`--keep-alive 0` unloads the model after a request; a duration such as `5m` sets
its idle timeout.

The opt-in `--tools` chat mode only enables a small arithmetic calculator. It
parses basic math expressions without `eval` and does not run arbitrary Python or
external commands. Image paths are attached to the first chat turn.

Chat history is not saved by default. Opt in with `--save-history`, or choose a
specific file with `--history-file`. Resume an existing transcript with
`--resume`; start it fresh with `--clear-history`. Saved files are JSONL under
`~/.huey/ollama_history/` by default and are created with owner-only permissions.
Use `--no-save` to disable persistence.

## Embeddings and RAG smoke check

The `embed` command batches a query and corpus through the embedding model, ranks
corpus paragraphs by cosine similarity, and can optionally pass the best matches
to a chat model for a local RAG check.

```bash
huey ollama embed "What does the scheduler do?" \
  --embed-model embeddinggemma --corpus-file ./docs/banana-brain.md \
  --top-k 3 --chat-model qwen3.6:35b
```

Without a corpus, the command checks the embedding model and reports vector size.
Use repeated `--corpus "..."` arguments for a small inline corpus or `--json` for
a structured report. Retrieved document text is treated as reference material in
the answer prompt.

## Benchmark and health report

```bash
huey ollama benchmark qwen3.6:35b --runs 3 --num-predict 128 \
  --json-out qwen-benchmark.json --csv-out qwen-benchmark.csv
huey ollama health
huey ollama health --json
```

The benchmark reports model load time, prompt and generation tokens per second,
wall time, and current Ollama-reported VRAM use. A cold first run and later warm
runs may differ. The health command reports server version, installed-model disk
sizes, and loaded-model VRAM; it returns a nonzero status when the server is
unreachable or inventory cannot be read.
