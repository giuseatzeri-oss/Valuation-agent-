"""The VT Capital valuation agent: Claude plus the deterministic valuation tools.

The agent keeps an append-only conversation history so follow-up questions
("now run it at a 9% WACC") reuse earlier tool results, and so thinking blocks
stay valid across turns. Each call streams text as it is generated.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, Optional

import anthropic

from .prompts import SYSTEM_PROMPT
from .tools import VALUATION_TOOLS

DEFAULT_MODEL = os.environ.get("VT_VALUATION_MODEL", "claude-opus-5-5")
DEFAULT_EFFORT = os.environ.get("VT_VALUATION_EFFORT", "high")
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AgentError(RuntimeError):
    """Raised when a turn cannot be completed."""


@dataclass
class ToolCallRecord:
    name: str
    input: dict
    output: str
    is_error: bool = False


@dataclass
class AgentTurn:
    text: str
    stop_reason: str | None
    model: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    refusal_category: str | None = None
    truncated: bool = False


class ValuationAgent:
    """Conversational valuation analyst for VT Capital.

    Args:
        client: An ``anthropic.Anthropic`` client. Defaults to one built from
            the environment (``ANTHROPIC_API_KEY`` or an ``ant auth login`` profile).
        model: Claude model id. Defaults to ``claude-opus-5-5``.
        effort: ``low`` .. ``max``. Defaults to ``high``.
        max_tokens: Per-response output cap. Raised to 64k automatically at
            ``xhigh`` or ``max`` effort.
        show_thinking: Return summarised reasoning in the stream.
        max_iterations: Cap on model turns within one request.
        fallbacks: Enable Anthropic's server-side refusal fallbacks.
    """

    def __init__(
        self,
        client: Optional[anthropic.Anthropic] = None,
        model: str = DEFAULT_MODEL,
        effort: str = DEFAULT_EFFORT,
        max_tokens: int = 32000,
        show_thinking: bool = False,
        max_iterations: int = 30,
        fallbacks: bool = True,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> None:
        if effort not in EFFORT_LEVELS:
            raise ValueError(f"effort must be one of {EFFORT_LEVELS}")
        self.client = client or anthropic.Anthropic()
        self.model = model
        self.effort = effort
        self.max_tokens = max(max_tokens, 64000) if effort in ("xhigh", "max") else max_tokens
        self.show_thinking = show_thinking
        self.max_iterations = max_iterations
        self.fallbacks = fallbacks
        self.system_prompt = system_prompt
        self.tools = list(VALUATION_TOOLS)
        self.messages: list[dict] = []

    # ------------------------------------------------------------------ public
    def reset(self) -> None:
        """Forget the conversation."""
        self.messages = []

    def ask(
        self,
        user_input: str,
        on_text: Optional[Callable[[str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[str, dict], None]] = None,
        on_tool_result: Optional[Callable[[str, str, bool], None]] = None,
    ) -> AgentTurn:
        """Send one user message and run the tool loop to completion.

        Callbacks receive streamed text deltas, thinking summaries, tool calls
        (name, input) and tool results (name, output, is_error).
        """
        if not user_input.strip():
            raise ValueError("user_input is empty")
        self.messages.append({"role": "user", "content": user_input})
        attempts = 0
        while True:
            attempts += 1
            try:
                return self._run_turn(on_text, on_thinking, on_tool_call, on_tool_result)
            except anthropic.APIError:
                raise
            except ValueError as exc:
                # The SDK raises ValueError when an eagerly streamed tool input
                # cannot be parsed. The history only holds completed turns, so
                # the request can simply be re-issued once.
                if attempts >= 2:
                    raise AgentError(f"model produced unparseable tool input twice: {exc}") from exc

    # ----------------------------------------------------------------- private
    def _request_params(self) -> dict:
        params: dict = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            system=[{"type": "text", "text": self.system_prompt, "cache_control": {"type": "ephemeral"}}],
            tools=self.tools,
            messages=self.messages,
            output_config={"effort": self.effort},
            max_iterations=self.max_iterations,
            stream=True,
        )
        if self.show_thinking:
            params["thinking"] = {"type": "adaptive", "display": "summarized"}
        if self.fallbacks:
            params["fallbacks"] = "default"
            params["betas"] = [FALLBACK_BETA]
        return params

    def _run_turn(self, on_text, on_thinking, on_tool_call, on_tool_result) -> AgentTurn:
        runner = self.client.beta.messages.tool_runner(**self._request_params())
        turn = AgentTurn(text="", stop_reason=None, model=self.model)
        appended = 0  # history entries added this turn, rolled back on failure
        final_message = None
        text_parts: list[str] = []
        try:
            for stream in runner:
                for event in stream:
                    etype = getattr(event, "type", None)
                    if etype == "text":
                        if on_text:
                            on_text(event.text)
                    elif etype == "thinking":
                        if on_thinking and event.thinking:
                            on_thinking(event.thinking)
                    elif etype == "content_block_start" and getattr(event.content_block, "type", None) == "tool_use":
                        if on_tool_call:
                            on_tool_call(event.content_block.name, {})
                message = stream.get_final_message()
                final_message = message
                self._accumulate_usage(turn, message)
                self.messages.append({"role": "assistant", "content": message.content})
                appended += 1
                text_parts.extend(b.text for b in message.content if b.type == "text")

                if message.stop_reason in ("refusal", "max_tokens"):
                    # Never run tools from a refused or truncated turn.
                    break
                tool_response = runner.generate_tool_call_response()
                if tool_response is not None:
                    self.messages.append(tool_response)
                    appended += 1
                    self._record_tool_calls(turn, message, tool_response, on_tool_result)
        except BaseException:
            del self.messages[len(self.messages) - appended :]
            raise

        if final_message is None:
            raise AgentError("the model returned no message")
        turn.stop_reason = final_message.stop_reason
        turn.model = final_message.model
        turn.text = "\n".join(p for p in text_parts if p.strip())
        if final_message.stop_reason == "refusal":
            details = getattr(final_message, "stop_details", None)
            turn.refusal_category = getattr(details, "category", None) if details else None
            explanation = getattr(details, "explanation", None) if details else None
            turn.text = (turn.text + "\n\n" if turn.text else "") + (
                "The model declined to complete this request" + (f" ({explanation})." if explanation else ".")
            )
        elif final_message.stop_reason == "max_tokens":
            turn.truncated = True
        return turn

    @staticmethod
    def _accumulate_usage(turn: AgentTurn, message) -> None:
        usage = getattr(message, "usage", None)
        if usage is None:
            return
        turn.input_tokens += getattr(usage, "input_tokens", 0) or 0
        turn.output_tokens += getattr(usage, "output_tokens", 0) or 0
        turn.cache_read_input_tokens += getattr(usage, "cache_read_input_tokens", 0) or 0

    @staticmethod
    def _record_tool_calls(turn: AgentTurn, message, tool_response: dict, on_tool_result) -> None:
        uses = {b.id: b for b in message.content if b.type == "tool_use"}
        for block in tool_response.get("content", []):
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                continue
            use = uses.get(block.get("tool_use_id"))
            name = use.name if use else "unknown"
            inputs = dict(use.input) if use else {}
            content = block.get("content", "")
            if isinstance(content, list):
                content = "".join(str(c.get("text", "")) if isinstance(c, dict) else str(c) for c in content)
            is_error = bool(block.get("is_error", False))
            turn.tool_calls.append(ToolCallRecord(name=name, input=inputs, output=str(content), is_error=is_error))
            if on_tool_result:
                on_tool_result(name, str(content), is_error)
