"""Exercise the streaming tool loop end to end against a mocked transport."""

import json

import anthropic
import httpx2 as httpx
import pytest

from vt_valuation_agent.agent import ValuationAgent


def _sse(events: list[dict]) -> bytes:
    return "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events).encode()


def _message_start(input_tokens: int = 50) -> dict:
    return {"type": "message_start", "message": {
        "id": "msg_test", "type": "message", "role": "assistant", "model": "claude-opus-5-5", "content": [],
        "stop_reason": None, "stop_sequence": None,
        "usage": {"input_tokens": input_tokens, "output_tokens": 1, "cache_read_input_tokens": 40, "cache_creation_input_tokens": 0},
    }}


TOOL_TURN = _sse([
    _message_start(),
    {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
    {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Running the IRR. "}},
    {"type": "content_block_stop", "index": 0},
    {"type": "content_block_start", "index": 1, "content_block": {"type": "tool_use", "id": "toolu_1", "name": "financial_calculator", "input": {}}},
    {"type": "content_block_delta", "index": 1, "delta": {"type": "input_json_delta", "partial_json": "{\"operation\": \"irr\", "}},
    {"type": "content_block_delta", "index": 1, "delta": {"type": "input_json_delta", "partial_json": "\"cash_flows\": [-100, 0, 121]}"}},
    {"type": "content_block_stop", "index": 1},
    {"type": "message_delta", "delta": {"stop_reason": "tool_use", "stop_sequence": None}, "usage": {"output_tokens": 30}},
    {"type": "message_stop"},
])

FINAL_TURN = _sse([
    _message_start(),
    {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
    {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "The IRR is 10.0%."}},
    {"type": "content_block_stop", "index": 0},
    {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}, "usage": {"output_tokens": 12}},
    {"type": "message_stop"},
])


def make_agent(requests: list[dict]) -> ValuationAgent:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append(body)
        last = body["messages"][-1]
        has_tool_result = isinstance(last.get("content"), list) and any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in last["content"]
        )
        payload = FINAL_TURN if has_tool_result else TOOL_TURN
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=payload)

    client = anthropic.Anthropic(api_key="test-key", http_client=anthropic.DefaultHttpxClient(transport=httpx.MockTransport(handler)))
    return ValuationAgent(client=client)


def test_streaming_tool_loop_runs_tool_and_keeps_history():
    requests: list[dict] = []
    agent = make_agent(requests)
    streamed: list[str] = []
    calls: list[str] = []
    results: list[tuple] = []

    turn = agent.ask(
        "What is the IRR of -100, 0, 121?",
        on_text=streamed.append,
        on_tool_call=lambda name, _i: calls.append(name),
        on_tool_result=lambda name, out, err: results.append((name, out, err)),
    )

    assert "".join(streamed) == "Running the IRR. The IRR is 10.0%."
    assert turn.text.endswith("The IRR is 10.0%.")
    assert turn.stop_reason == "end_turn"
    assert calls == ["financial_calculator"]
    assert len(turn.tool_calls) == 1
    rec = turn.tool_calls[0]
    assert rec.name == "financial_calculator" and not rec.is_error
    assert json.loads(rec.output)["result"] == pytest.approx(0.10, abs=1e-6)
    assert results[0][0] == "financial_calculator" and results[0][2] is False
    assert turn.input_tokens == 100 and turn.output_tokens == 42 and turn.cache_read_input_tokens == 80

    # Two API calls: the tool turn and the final answer.
    assert len(requests) == 2
    first, second = requests
    assert first["model"] == "claude-opus-5-5"
    assert first["stream"] is True
    assert first["fallbacks"] == "default"
    assert first["output_config"] == {"effort": "high"}
    assert first["system"][0]["cache_control"] == {"type": "ephemeral"}
    tool_names = {t["name"] for t in first["tools"]}
    assert "dcf_valuation" in tool_names and all(t.get("eager_input_streaming") for t in first["tools"])
    # The second request replays the assistant tool_use turn and the tool result.
    assert second["messages"][1]["role"] == "assistant"
    assert second["messages"][2]["content"][0]["type"] == "tool_result"
    assert second["messages"][2]["content"][0]["tool_use_id"] == "toolu_1"

    # History is append-only: user, assistant(tool_use), user(tool_result), assistant(final).
    assert [m["role"] for m in agent.messages] == ["user", "assistant", "user", "assistant"]

    # A follow-up carries the full history: the four earlier entries plus the new user turn.
    before = len(requests)
    agent.ask("Thanks.", on_text=None)
    assert len(requests[before]["messages"]) == 5
    assert requests[before]["messages"][-1] == {"role": "user", "content": "Thanks."}


def test_history_rolled_back_when_request_fails():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"type": "error", "error": {"type": "api_error", "message": "boom"}})

    client = anthropic.Anthropic(
        api_key="test-key", max_retries=0,
        http_client=anthropic.DefaultHttpxClient(transport=httpx.MockTransport(handler)),
    )
    agent = ValuationAgent(client=client)
    with pytest.raises(anthropic.InternalServerError):
        agent.ask("hello")
    # The failed user turn stays (it was the user's), but nothing partial from the model.
    assert [m["role"] for m in agent.messages] == ["user"]
