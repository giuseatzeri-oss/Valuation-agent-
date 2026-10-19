"""Command-line interface for the VT Capital valuation agent.

    vt-valuation-agent ask "Value a company with ..." [--file notes.md] [--save out.md]
    vt-valuation-agent chat
    vt-valuation-agent engine examples/sample_target.json [--save out.md]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import anthropic

from .agent import DEFAULT_EFFORT, DEFAULT_MODEL, EFFORT_LEVELS, AgentError, ValuationAgent
from .report import load_spec, render_markdown, run_engine

SUBCOMMANDS = ("ask", "chat", "engine")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vt-valuation-agent", description="VT Capital valuation agent")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_model_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--model", default=DEFAULT_MODEL, help=f"Claude model id (default {DEFAULT_MODEL})")
        p.add_argument("--effort", default=DEFAULT_EFFORT, choices=EFFORT_LEVELS, help="reasoning effort")
        p.add_argument("--show-thinking", action="store_true", help="print summarised reasoning")
        p.add_argument("--quiet-tools", action="store_true", help="do not print tool call progress")
        p.add_argument("--no-fallbacks", action="store_true", help="disable server-side refusal fallbacks")

    ask = sub.add_parser("ask", help="one question, streamed answer")
    ask.add_argument("prompt", nargs="+", help="the request")
    ask.add_argument("--file", action="append", default=[], help="attach a text/JSON/CSV file as context (repeatable)")
    ask.add_argument("--save", help="write the final answer to this markdown file")
    add_model_args(ask)

    chat = sub.add_parser("chat", help="interactive multi-turn session")
    chat.add_argument("--file", action="append", default=[], help="attach context files to the first turn")
    add_model_args(chat)

    eng = sub.add_parser("engine", help="run the deterministic engine from a JSON spec (no API key needed)")
    eng.add_argument("spec", help="path to the JSON spec")
    eng.add_argument("--save", help="write the markdown report to this file")
    eng.add_argument("--json", action="store_true", help="print raw JSON results instead of markdown")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in SUBCOMMANDS and not argv[0].startswith("-"):
        argv.insert(0, "ask")  # allow: vt-valuation-agent "free text question"
    args = build_parser().parse_args(argv)

    if args.command == "engine":
        return _run_engine(args)

    try:
        agent = ValuationAgent(
            model=args.model, effort=args.effort, show_thinking=args.show_thinking, fallbacks=not args.no_fallbacks
        )
    except anthropic.AnthropicError as exc:
        print(f"Could not create the Anthropic client: {exc}", file=sys.stderr)
        print("Set ANTHROPIC_API_KEY or run `ant auth login`. Use the `engine` subcommand for offline runs.", file=sys.stderr)
        return 2

    if args.command == "ask":
        prompt = _with_files(" ".join(args.prompt), args.file)
        try:
            turn = _stream_turn(agent, prompt, args)
        except (anthropic.APIError, AgentError) as exc:
            print(f"\nRequest failed: {exc}", file=sys.stderr)
            return 1
        except TypeError as exc:
            if not _is_auth_error(exc):
                raise
            _print_auth_help(exc)
            return 2
        if args.save:
            Path(args.save).write_text(turn.text + "\n", encoding="utf-8")
            print(f"\nSaved to {args.save}")
        return 0

    return _chat(agent, args)


def _is_auth_error(exc: BaseException) -> bool:
    return "authentication method" in str(exc).lower()


def _print_auth_help(exc: BaseException) -> None:
    print(f"\nNo Anthropic credentials found: {exc}", file=sys.stderr)
    print("Set ANTHROPIC_API_KEY or run `ant auth login`. The `engine` subcommand works offline.", file=sys.stderr)


def _run_engine(args) -> int:
    spec = load_spec(args.spec)
    results = run_engine(spec)
    if args.json:
        text = json.dumps(_jsonable(results), indent=2)
    else:
        text = render_markdown(results)
    print(text)
    if args.save:
        Path(args.save).write_text(text + "\n", encoding="utf-8")
        print(f"\nSaved to {args.save}", file=sys.stderr)
    return 0


def _jsonable(obj):
    if hasattr(obj, "to_dict"):
        return _jsonable(obj.to_dict())
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj


def _with_files(prompt: str, files: list[str]) -> str:
    if not files:
        return prompt
    parts = [prompt, ""]
    for f in files:
        path = Path(f)
        parts.append(f"<attached_file name=\"{path.name}\">\n{path.read_text(encoding='utf-8')}\n</attached_file>")
    return "\n".join(parts)


def _stream_turn(agent: ValuationAgent, prompt: str, args):
    def on_text(delta: str) -> None:
        sys.stdout.write(delta)
        sys.stdout.flush()

    def on_thinking(delta: str) -> None:
        sys.stderr.write(f"\033[2m{delta}\033[0m")
        sys.stderr.flush()

    def on_tool_call(name: str, _inputs: dict) -> None:
        if not args.quiet_tools:
            sys.stderr.write(f"\n\033[36m[tool] {name}\033[0m\n")
            sys.stderr.flush()

    def on_tool_result(name: str, output: str, is_error: bool) -> None:
        if not args.quiet_tools and is_error:
            sys.stderr.write(f"\033[33m[tool error] {name}: {output[:300]}\033[0m\n")
            sys.stderr.flush()

    turn = agent.ask(prompt, on_text=on_text, on_thinking=on_thinking if args.show_thinking else None,
                     on_tool_call=on_tool_call, on_tool_result=on_tool_result)
    print()
    if turn.truncated:
        print("[answer was cut off at the output limit; ask it to continue or raise --effort/max_tokens]", file=sys.stderr)
    if turn.refusal_category:
        print(f"[request declined: category {turn.refusal_category}]", file=sys.stderr)
    print(
        f"[{turn.model} | {len(turn.tool_calls)} tool calls | in {turn.input_tokens:,} / out {turn.output_tokens:,} tokens"
        f" | cache read {turn.cache_read_input_tokens:,}]",
        file=sys.stderr,
    )
    return turn


def _chat(agent: ValuationAgent, args) -> int:
    print("VT Capital valuation agent. Type your request; 'reset' clears the conversation, 'quit' exits.")
    first = True
    while True:
        try:
            line = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        if line.lower() in ("quit", "exit"):
            return 0
        if line.lower() == "reset":
            agent.reset()
            print("conversation cleared")
            continue
        prompt = _with_files(line, args.file) if first else line
        first = False
        print("\nagent> ", end="", flush=True)
        try:
            _stream_turn(agent, prompt, args)
        except (anthropic.APIError, AgentError) as exc:
            print(f"\nRequest failed: {exc}", file=sys.stderr)
        except TypeError as exc:
            if not _is_auth_error(exc):
                raise
            _print_auth_help(exc)
            return 2


if __name__ == "__main__":
    sys.exit(main())
