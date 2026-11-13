"""Operator-facing Ollama model and chat commands for HueyOS."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .ollama_operations import (
    cmd_benchmark,
    cmd_chat,
    cmd_create,
    cmd_embed,
    cmd_generate,
    cmd_health,
    cmd_stop,
)


def _load_client(host: str | None) -> tuple[Any, Any]:
    """Load the optional Ollama client without making it a core dependency."""

    try:
        from ollama import Client, ResponseError
    except ImportError as exc:
        raise RuntimeError(
            "Ollama commands require the optional ML dependencies. "
            "Install HueyOS with its 'ml' extra."
        ) from exc
    return Client(host=host), ResponseError


def _size_gib(value: int | None) -> str:
    return f"{(value or 0) / (1024**3):.2f} GiB"


def _progress(progress: Iterable[Any], action: str) -> None:
    for item in progress:
        status = item.get("status", "") or ""
        completed = item.get("completed")
        total = item.get("total")
        if completed is not None and total:
            print(
                f"\r{action}: {status} "
                f"{completed / total * 100:.1f}% ({completed}/{total})",
                end="",
                flush=True,
            )
        else:
            print(f"\r{action}: {status}", end="", flush=True)
    print(f"\n{action} complete.")


def _cmd_list(client: Any, _args: argparse.Namespace) -> int:
    models = client.list().models
    if not models:
        print("No local models found.")
        return 0
    print(f"{'MODEL':<42} {'SIZE':>12}  MODIFIED")
    for model in models:
        name = model.model or "(unnamed)"
        print(f"{name:<42} {_size_gib(model.size):>12}  {model.modified_at or '-'}")
    return 0


def _cmd_show(client: Any, args: argparse.Namespace) -> int:
    info = client.show(args.model)
    print(f"Model: {args.model}")
    for label, value in (
        ("Details", info.details.model_dump(exclude_none=True) if info.details else {}),
        ("Parameters", info.parameters),
        ("Template", info.template),
        ("Capabilities", info.capabilities),
        ("Modelfile", info.modelfile),
    ):
        print(f"\n{label}:")
        print(value if value else "(none)")
    return 0


def _cmd_pull(client: Any, args: argparse.Namespace) -> int:
    _progress(client.pull(args.model, stream=True), f"Pulling {args.model}")
    return 0


def _cmd_push(client: Any, args: argparse.Namespace) -> int:
    _progress(client.push(args.model, stream=True), f"Pushing {args.model}")
    return 0


def _cmd_create(client: Any, args: argparse.Namespace) -> int:
    return cmd_create(client, args)


def _cmd_copy(client: Any, args: argparse.Namespace) -> int:
    result = client.copy(args.source, args.destination)
    print(result.status or f"Copied {args.source} to {args.destination}.")
    return 0


def _cmd_delete(client: Any, args: argparse.Namespace) -> int:
    if not args.yes:
        if not sys.stdin.isatty():
            raise RuntimeError("Deletion needs confirmation; rerun with --yes.")
        confirmation = input(
            f"Type the exact model name '{args.model}' to delete it: "
        ).strip()
        if confirmation != args.model:
            print("Deletion cancelled.")
            return 1
    client.delete(args.model)
    print(f"Deleted {args.model}.")
    return 0


def _cmd_ps(client: Any, _args: argparse.Namespace) -> int:
    models = client.ps().models
    if not models:
        print("No models are currently loaded.")
        return 0
    print(f"{'MODEL':<42} {'MEMORY':>12} {'VRAM':>12}  EXPIRES")
    for model in models:
        name = model.name or model.model or "(unnamed)"
        print(
            f"{name:<42} {_size_gib(model.size):>12} "
            f"{_size_gib(model.size_vram):>12}  {model.expires_at or '-'}"
        )
    return 0


def _cmd_generate(client: Any, args: argparse.Namespace) -> int:
    return cmd_generate(client, args)


def _cmd_chat(client: Any, args: argparse.Namespace) -> int:
    return cmd_chat(client, args)


def _cmd_stop(client: Any, args: argparse.Namespace) -> int:
    return cmd_stop(client, args)


def _cmd_embed(client: Any, args: argparse.Namespace) -> int:
    return cmd_embed(client, args)


def _cmd_benchmark(client: Any, args: argparse.Namespace) -> int:
    return cmd_benchmark(client, args)


def _cmd_health(client: Any, args: argparse.Namespace) -> int:
    return cmd_health(client, args)


def _add_runtime_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--preset", choices=("qwen-8k", "deterministic"))
    parser.add_argument("--num-ctx", type=int)
    parser.add_argument("--num-predict", type=int)
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--top-p", type=float)
    parser.add_argument("--top-k", type=int)
    parser.add_argument("--system", help="System prompt.")
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "--format-json", action="store_true", help="Request JSON output."
    )
    format_group.add_argument(
        "--format-schema",
        type=Path,
        help="JSON schema file for structured output.",
    )
    parser.add_argument(
        "--keep-alive",
        help="Model residency duration, such as 5m; use 0 to unload after the request.",
    )


def _run(args: argparse.Namespace) -> int:
    try:
        client, response_error = _load_client(args.host)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        with client:
            return args.handler(client, args)
    except response_error as exc:
        print(f"Ollama error: {exc.error}", file=sys.stderr)
        return 1
    except ConnectionError as exc:
        print(f"Cannot connect to Ollama: {exc}", file=sys.stderr)
        print(
            "Check that Ollama is running and that --host is correct.",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        print(f"Ollama command failed: {exc}", file=sys.stderr)
        return 1


def _dispatch(handler: Any):
    def run(args: argparse.Namespace) -> int:
        args.handler = handler
        return _run(args)

    return run


def register_ollama_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register the optional Ollama operator CLI under ``huey ollama``."""

    parser = subparsers.add_parser(
        "ollama", help="Manage local Ollama models and run chat or generation."
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Ollama server URL (defaults to OLLAMA_HOST or localhost:11434).",
    )
    actions = parser.add_subparsers(dest="ollama_command", required=True)

    actions.add_parser("list", help="List locally installed models.").set_defaults(
        handler=_dispatch(_cmd_list)
    )
    show = actions.add_parser("show", help="Show a model's configuration.")
    show.add_argument("model")
    show.set_defaults(handler=_dispatch(_cmd_show))

    for command, help_text, handler in (
        ("pull", "Download a model from the Ollama registry.", _cmd_pull),
        ("push", "Upload a model to the Ollama registry.", _cmd_push),
    ):
        item = actions.add_parser(command, help=help_text)
        item.add_argument("model")
        item.set_defaults(handler=_dispatch(handler))

    create = actions.add_parser(
        "create", help="Create a model from a local base model."
    )
    create.add_argument("model", help="Name for the new model.")
    create.add_argument("--from", dest="base_model")
    create.add_argument(
        "--modelfile", type=Path, help="Use the installed Ollama CLI and this file."
    )
    create.add_argument("--system", help="Optional system prompt.")
    create.add_argument("--template", help="Optional template string.")
    create.add_argument("--quantize", help="Optional quantization method.")
    create.add_argument(
        "--param",
        dest="parameter",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Model parameter; repeat for multiple values.",
    )
    create.set_defaults(handler=_dispatch(_cmd_create))

    copy = actions.add_parser("copy", help="Copy a model to another local name.")
    copy.add_argument("source")
    copy.add_argument("destination")
    copy.set_defaults(handler=_dispatch(_cmd_copy))

    delete = actions.add_parser("delete", help="Delete a locally installed model.")
    delete.add_argument("model")
    delete.add_argument(
        "--yes",
        action="store_true",
        help="Confirm deletion without an interactive prompt.",
    )
    delete.set_defaults(handler=_dispatch(_cmd_delete))

    actions.add_parser("ps", help="List currently loaded models.").set_defaults(
        handler=_dispatch(_cmd_ps)
    )

    stop = actions.add_parser("stop", help="Unload a model from memory.")
    stop.add_argument("model", nargs="?")
    stop.add_argument("--all", dest="all_models", action="store_true")
    stop.set_defaults(handler=_dispatch(_cmd_stop))

    embed = actions.add_parser(
        "embed", help="Embed text and optionally run a local RAG smoke check."
    )
    embed.add_argument("query", nargs="+", help="Query text to embed.")
    embed.add_argument("--embed-model", default="embeddinggemma")
    embed.add_argument(
        "--corpus-file", type=Path, help="Text file split by paragraphs."
    )
    embed.add_argument(
        "--corpus", action="append", default=[], help="Corpus text; repeatable."
    )
    embed.add_argument("--top-k", type=int, default=3)
    embed.add_argument("--chat-model", help="Answer with top retrieved passages.")
    embed.add_argument("--json", action="store_true", help="Emit a JSON report.")
    embed.set_defaults(handler=_dispatch(_cmd_embed))

    generate = actions.add_parser("generate", help="Generate text from a prompt.")
    generate.add_argument("model")
    generate.add_argument("prompt", nargs="+", help="Prompt text.")
    _add_runtime_options(generate)
    generate.add_argument("--no-stream", action="store_true")
    generate.set_defaults(handler=_dispatch(_cmd_generate))

    chat = actions.add_parser("chat", help="Start an interactive multi-turn chat.")
    chat.add_argument("model", nargs="?", default="qwen3.6:35b")
    _add_runtime_options(chat)
    chat.add_argument(
        "--image", action="append", default=[], help="Attach an image file."
    )
    chat.add_argument(
        "--tools",
        action="store_true",
        help="Enable the allowlisted, side-effect-free arithmetic tool.",
    )
    chat.add_argument("--no-stream", action="store_true")
    chat.add_argument("--save-history", action="store_true")
    chat.add_argument("--history-file", type=Path)
    chat.add_argument("--resume", action="store_true")
    chat.add_argument("--clear-history", action="store_true")
    chat.add_argument("--no-save", action="store_true")
    chat.set_defaults(handler=_dispatch(_cmd_chat))

    benchmark = actions.add_parser(
        "benchmark", help="Measure generation speed, load time, and VRAM use."
    )
    benchmark.add_argument("model")
    benchmark.add_argument(
        "--prompt",
        default="Explain the significance of the Turing test in three sentences.",
    )
    benchmark.add_argument("--runs", type=int, default=3)
    benchmark.add_argument("--num-predict", type=int)
    benchmark.add_argument("--json-out", type=Path)
    benchmark.add_argument("--csv-out", type=Path)
    benchmark.add_argument("--system")
    benchmark.add_argument("--preset", choices=("qwen-8k", "deterministic"))
    benchmark.add_argument("--num-ctx", type=int)
    benchmark.add_argument("--temperature", type=float)
    benchmark.add_argument("--top-p", type=float)
    benchmark.add_argument("--top-k", type=int)
    benchmark.add_argument("--keep-alive")
    benchmark.set_defaults(handler=_dispatch(_cmd_benchmark))

    health = actions.add_parser(
        "health", help="Report server version, installed models, and loaded VRAM."
    )
    health.add_argument("--json", action="store_true")
    health.set_defaults(handler=_dispatch(_cmd_health))


__all__ = ["register_ollama_commands"]
