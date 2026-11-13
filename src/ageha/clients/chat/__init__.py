"""Small client for OpenAI-compatible chat completion APIs."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import requests


class ChatError(RuntimeError):
    """Raised when a chat request or provider response is invalid."""


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Reply:
    content: str
    tool_calls: tuple[ToolCall, ...] = ()
    finish: bool = True


_THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_thinking(text: str) -> str:
    return _THINK_PATTERN.sub("", text).strip()


def _message_dict(message: Mapping[str, Any] | object) -> dict[str, Any]:
    if isinstance(message, Mapping):
        return dict(message)
    as_dict = getattr(message, "as_dict", None)
    if callable(as_dict):
        return as_dict()
    raise TypeError("messages must be mappings or provide as_dict()")


def _tool_dict(tool: Mapping[str, Any] | object) -> dict[str, Any]:
    if isinstance(tool, Mapping):
        data = dict(tool)
        if "function" in data:
            return data
        return {"type": "function", "function": data}
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


def _parse_arguments(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


class Chat:
    """OpenAI-compatible chat client shared by Ageha applications.

    Provider-specific filenames are unnecessary: configure the endpoint and model,
    e.g. ``Chat(api_key=..., base_url="https://api.deepseek.com/v1", model="deepseek-chat")``.
    """

    supports_streaming = True

    def __init__(
        self,
        *,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str,
        timeout: float = 60.0,
        extra_body: Mapping[str, Any] | None = None,
    ) -> None:
        if not base_url.strip():
            raise ValueError("base_url is required")
        if not model.strip():
            raise ValueError("model is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.extra_body = dict(extra_body or {})
        self.session = requests.Session()

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ChatError("Chat API key is not configured")
        return {"Authorization": f"Bearer {self.api_key}"}

    def check_connection(self) -> None:
        response = self.session.get(
            f"{self.base_url}/models", headers=self._headers(), timeout=min(self.timeout, 15.0)
        )
        response.raise_for_status()

    def complete(
        self,
        messages: Sequence[Mapping[str, Any] | object],
        *,
        temperature: float = 0.9,
        max_tokens: int = 512,
    ) -> str:
        payload = self._payload(messages, temperature, max_tokens)
        response = self.session.post(
            f"{self.base_url}/chat/completions",
            headers=self._headers(),
            json={**payload, "stream": False},
            timeout=self.timeout,
        )
        response.raise_for_status()
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise ChatError("Chat API returned an invalid response") from error
        return _strip_thinking(str(content or ""))

    def complete_agent(
        self,
        messages: Sequence[Mapping[str, Any] | object],
        tools: Sequence[Mapping[str, Any] | object],
        *,
        temperature: float = 0.9,
        max_tokens: int = 1024,
        on_delta: Callable[[str], None] | None = None,
    ) -> Reply:
        payload = self._payload(messages, temperature, max_tokens)
        payload.update({"stream": on_delta is not None, "tools": [_tool_dict(t) for t in tools]})
        response = self.session.post(
            f"{self.base_url}/chat/completions",
            headers=self._headers(), json=payload, timeout=self.timeout,
            stream=on_delta is not None,
        )
        response.raise_for_status()
        if on_delta is not None:
            return self._stream_reply(response, on_delta)
        try:
            message = response.json()["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as error:
            raise ChatError("Chat API returned an invalid response") from error
        calls = tuple(
            ToolCall(
                id=str(item["id"]),
                name=str(item["function"]["name"]),
                arguments=_parse_arguments(item["function"].get("arguments", "{}")),
            )
            for item in message.get("tool_calls", [])
            if item.get("id") and item.get("function", {}).get("name")
        )
        return Reply(_strip_thinking(str(message.get("content") or "")), calls, not calls)

    def _payload(self, messages: Sequence[Mapping[str, Any] | object], temperature: float,
                 max_tokens: int) -> dict[str, Any]:
        return {
            **self.extra_body,
            "model": self.model,
            "messages": [_message_dict(item) for item in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def _stream_reply(self, response: requests.Response,
                      on_delta: Callable[[str], None]) -> Reply:
        content: list[str] = []
        calls: dict[int, dict[str, str]] = {}
        filter_ = _ThinkingStreamFilter()
        with response:
            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    break
                try:
                    choices = json.loads(raw).get("choices") or []
                except json.JSONDecodeError:
                    continue
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                text = delta.get("content")
                if isinstance(text, str) and text:
                    content.append(text)
                    visible = filter_.feed(text)
                    if visible:
                        on_delta(visible)
                for call in delta.get("tool_calls") or []:
                    index = int(call.get("index", 0))
                    item = calls.setdefault(index, {"id": "", "name": "", "arguments": ""})
                    item["id"] += str(call.get("id") or "")
                    function = call.get("function") or {}
                    item["name"] += str(function.get("name") or "")
                    item["arguments"] += str(function.get("arguments") or "")
        tail = filter_.feed("", final=True)
        if tail:
            on_delta(tail)
        parsed = tuple(
            ToolCall(item["id"], item["name"], _parse_arguments(item["arguments"] or "{}"))
            for _, item in sorted(calls.items()) if item["id"] and item["name"]
        )
        return Reply(_strip_thinking("".join(content)), parsed, not parsed)


class _ThinkingStreamFilter:
    _OPEN = "<think>"
    _CLOSE = "</think>"

    def __init__(self) -> None:
        self.buffer = ""
        self.in_thought = False

    def feed(self, chunk: str, *, final: bool = False) -> str:
        self.buffer += chunk
        visible: list[str] = []
        while self.buffer:
            if self.in_thought:
                end = self.buffer.find(self._CLOSE)
                if end < 0:
                    keep = 0 if final else _suffix_prefix_length(self.buffer, self._CLOSE)
                    self.buffer = self.buffer[-keep:] if keep else ""
                    break
                self.buffer = self.buffer[end + len(self._CLOSE):]
                self.in_thought = False
                continue
            start = self.buffer.find(self._OPEN)
            if start >= 0:
                visible.append(self.buffer[:start])
                self.buffer = self.buffer[start + len(self._OPEN):]
                self.in_thought = True
                continue
            keep = 0 if final else _suffix_prefix_length(self.buffer, self._OPEN)
            safe_length = len(self.buffer) - keep
            if safe_length:
                visible.append(self.buffer[:safe_length])
            self.buffer = self.buffer[safe_length:]
            break
        return "".join(visible)


def _suffix_prefix_length(value: str, marker: str) -> int:
    return max((size for size in range(1, min(len(value), len(marker) - 1) + 1)
                if value.endswith(marker[:size])), default=0)


__all__ = ["Chat", "ChatError", "Reply", "ToolCall"]
