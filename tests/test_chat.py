from __future__ import annotations

import pytest

from ageha import Chat, ChatError


class Response:
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class Session:
    def __init__(self, payload):
        self.response = Response(payload)

    def post(self, _url, **_kwargs):
        return self.response


def client(payload):
    chat = Chat(api_key="test", model="test-model")
    chat.session = Session(payload)
    return chat


def test_complete_reports_reasoning_only_response_without_exposing_reasoning():
    chat = client({
        "base_resp": {"status_code": 0},
        "choices": [{
            "finish_reason": "length",
            "message": {"role": "assistant", "reasoning_content": "private chain of thought"},
        }],
    })

    with pytest.raises(ChatError, match="no user-visible message content.*finish_reason=length") as error:
        chat.complete([{"role": "user", "content": "hello"}])

    assert "private chain of thought" not in str(error.value)


def test_complete_reports_minimax_base_response_error():
    chat = client({
        "base_resp": {"status_code": 1004, "status_msg": "invalid request"},
    })

    with pytest.raises(ChatError, match=r"provider rejected the request \(status 1004\): invalid request"):
        chat.complete([{"role": "user", "content": "hello"}])


def test_complete_agent_accepts_normal_openai_compatible_response():
    chat = client({
        "base_resp": {"status_code": 0},
        "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "你好"}}],
    })

    assert chat.complete_agent([{"role": "user", "content": "hello"}], []).content == "你好"


def test_complete_agent_accepts_tool_call_without_text_content():
    chat = client({"choices": [{"finish_reason": "tool_calls", "message": {
        "role": "assistant", "content": None, "tool_calls": [{
            "id": "call_clock", "type": "function",
            "function": {"name": "clock", "arguments": "{}"},
        }],
    }}]})
    reply = chat.complete_agent([{"role": "user", "content": "time?"}], [])
    assert reply.content == ""
    assert reply.tool_calls[0].name == "clock"
    assert reply.tool_calls[0].id == "call_clock"


def test_complete_agent_rejects_reasoning_only_response():
    chat = client({"choices": [{"finish_reason": "length", "message": {
        "content": None, "reasoning_content": "private reasoning",
    }}]})
    with pytest.raises(ChatError, match="no user-visible message content") as error:
        chat.complete_agent([{"role": "user", "content": "hello"}], [])
    assert "private reasoning" not in str(error.value)
