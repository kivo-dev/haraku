"""Anthropic Messages API adapter.

!! Written from knowledge of the public API (POST /v1/messages, x-api-key, anthropic-version header,
tool_use / tool_result content blocks). It has NOT been run against the live service: no key and no
network were available when it was written. Parsing/serialisation is unit-tested with fake responses.
Check it once with a real key (see README) before relying on it."""
import json
from typing import Any, Optional

from ..errors import LLMBadResponse
from ..types import LLMResponse, Message, ToolCall, ToolSpec, Usage
from .base import Poster, httpx_post, post_with_retry

API_VERSION = "2023-06-01"


def build_messages(messages: list[Message]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    pending_results: list[dict[str, Any]] = []

    def flush() -> None:
        if pending_results:
            out.append({"role": "user", "content": list(pending_results)})
            pending_results.clear()

    for m in messages:
        if m.role == "tool":
            # all tool results answering one assistant turn must travel in ONE user message
            pending_results.append({"type": "tool_result", "tool_use_id": m.tool_call_id, "content": m.content})
            continue
        flush()
        if m.role == "assistant":
            blocks: list[dict[str, Any]] = []
            if m.content:
                blocks.append({"type": "text", "text": m.content})
            for c in m.tool_calls:
                blocks.append({"type": "tool_use", "id": c.id, "name": c.name, "input": c.arguments})
            out.append({"role": "assistant", "content": blocks or [{"type": "text", "text": ""}]})
        else:
            out.append({"role": "user", "content": m.content})
    flush()
    return out


def parse_response(data: dict[str, Any], model: str) -> LLMResponse:
    try:
        blocks = data["content"]
        text_parts: list[str] = []
        calls: list[ToolCall] = []
        for b in blocks:
            if b.get("type") == "text":
                text_parts.append(b.get("text", ""))
            elif b.get("type") == "tool_use":
                args = b.get("input")
                calls.append(ToolCall(str(b["id"]), str(b["name"]), args if isinstance(args, dict) else {"__invalid__": True}))
        u = data.get("usage") or {}
        usage = Usage(int(u.get("input_tokens", 0)), int(u.get("output_tokens", 0)))
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise LLMBadResponse("Unexpected response shape from the AI provider") from exc
    return LLMResponse("".join(text_parts), calls, usage, str(data.get("model", model)))


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str = "https://api.anthropic.com",
        timeout_s: float = 30.0,
        max_tokens: int = 1024,
        retries: int = 2,
        post: Optional[Poster] = None,
        sleep=None,
    ):
        self._key, self.model = api_key, model
        self._url = base_url.rstrip("/") + "/v1/messages"
        self._timeout, self._max_tokens, self._retries = timeout_s, max_tokens, retries
        self._post, self._sleep = post or httpx_post, sleep

    async def complete(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMResponse:
        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self._max_tokens,
            "system": system,
            "messages": build_messages(messages),
        }
        if tools:
            body["tools"] = [{"name": t.name, "description": t.description, "input_schema": t.parameters} for t in tools]
        headers = {"x-api-key": self._key, "anthropic-version": API_VERSION, "content-type": "application/json"}
        data = await post_with_retry(
            self._post, self._url, headers, body, provider=self.name, timeout_s=self._timeout, retries=self._retries, sleep=self._sleep
        )
        return parse_response(data, self.model)
