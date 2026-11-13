"""Operator-facing Ollama model and chat commands for HueyOS."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from typing import Any


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
    result = client.create(
        model=args.model,
        from_=args.base_model,
        system=args.system,
    )
    print(result.status or f"Created {args.model}.")
    return 0


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
    stream = client.generate(
        model=args.model,
        prompt=" ".join(args.prompt),
        stream=True,
    )
    for chunk in stream:
        print(chunk.get("response", "") or "", end="", flush=True)
    print()
    return 0


def _cmd_chat(client: Any, args: argparse.Namespace) -> int:
    history: list[dict[str, str]] = []
    print(f"Chatting with {args.model}. Type 'exit' or 'quit' to stop.")
    while True:
        try:
            user_text = input("You: ").strip()
        except EOFError:
            print()
            return 0
        if user_text.lower() in {"exit", "quit"}:
            return 0
        if not user_text:
            continue

        history.append({"role": "user", "content": user_text})
        try:
            response_parts: list[str] = []
            for chunk in client.chat(model=args.model, messages=history, stream=True):
                message = chunk.get("message", {})
                content = message.get("content", "") if message else ""
                if content:
                    response_parts.append(content)
                    print(content, end="", flush=True)
            print("\n")
            history.append(
                {"role": "assistant", "content": "".join(response_parts)}
            )
        except Exception as exc:
            history.pop()
            print(f"\nOllama request failed: {exc}\n", file=sys.stderr)


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
        print("Check that Ollama is running and that --host is correct.", file=sys.stderr)
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
    create.add_argument("--from", dest="base_model", required=True)
    create.add_argument("--system", default=None, help="Optional system prompt.")
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
    generate = actions.add_parser("generate", help="Generate text from a prompt.")
    generate.add_argument("model")
    generate.add_argument("prompt", nargs="+", help="Prompt text.")
    generate.set_defaults(handler=_dispatch(_cmd_generate))

    chat = actions.add_parser("chat", help="Start an interactive multi-turn chat.")
    chat.add_argument("model", nargs="?", default="llama3.2")
    chat.set_defaults(handler=_dispatch(_cmd_chat))


__all__ = ["register_ollama_commands"]
