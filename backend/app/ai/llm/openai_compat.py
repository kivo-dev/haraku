"""OpenAI-compatible Chat Completions adapter (OpenAI, OpenRouter, vLLM, Ollama, ... anything that
speaks POST {base_url}/chat/completions with `tools`).

!! Same status as the Anthropic adapter: written from knowledge of the public API, unit-tested with
fake responses, NOT yet run against a live service. Some newer OpenAI models want `max_completion_tokens`
instead of `max_tokens`: if the provider answers 400, change the field name in `complete()`."""
import json
from typing import Any, Optional

from ..errors import LLMBadResponse
from ..types import LLMResponse, Message, ToolCall, ToolSpec, Usage
from .base import Poster, httpx_post, post_with_retry


def build_messages(system: str, messages: list[Message]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for m in messages:
        if m.role == "tool":
            out.append({"role": "tool", "tool_call_id": m.tool_call_id, "content": m.content})
        elif m.role == "assistant":
            msg: dict[str, Any] = {"role": "assistant", "content": m.content or None}
            if m.tool_calls:
                msg["tool_calls"] = [
                    {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": json.dumps(c.arguments, ensure_ascii=False)}}
                    for c in m.tool_calls
                ]
            out.append(msg)
        else:
            out.append({"role": "user", "content": m.content})
    return out


def parse_response(data: dict[str, Any], model: str) -> LLMResponse:
    try:
        msg = data["choices"][0]["message"]
        calls: list[ToolCall] = []
        for c in msg.get("tool_calls") or []:
            raw = c["function"].get("arguments") or "{}"
            try:
                args = json.loads(raw)
                if not isinstance(args, dict):
                    raise ValueError
            except ValueError:
                args = {"__invalid_json__": str(raw)[:80]}  # rejected by validation, the model is told and can retry
            calls.append(ToolCall(str(c["id"]), str(c["function"]["name"]), args))
        u = data.get("usage") or {}
        usage = Usage(int(u.get("prompt_tokens", 0)), int(u.get("completion_tokens", 0)))
        text = msg.get("content") or ""
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise LLMBadResponse("Unexpected response shape from the AI provider") from exc
    return LLMResponse(text, calls, usage, str(data.get("model", model)))


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str = "https://api.openai.com/v1",
        timeout_s: float = 30.0,
        max_tokens: int = 1024,
        retries: int = 2,
        post: Optional[Poster] = None,
        sleep=None,
    ):
        self._key, self.model = api_key, model
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._timeout, self._max_tokens, self._retries = timeout_s, max_tokens, retries
        self._post, self._sleep = post or httpx_post, sleep

    async def complete(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMResponse:
        body: dict[str, Any] = {"model": self.model, "max_tokens": self._max_tokens, "messages": build_messages(system, messages)}
        if tools:
            body["tools"] = [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}} for t in tools]
        headers = {"content-type": "application/json"}
        if self._key:
            headers["authorization"] = f"Bearer {self._key}"
        data = await post_with_retry(
            self._post, self._url, headers, body, provider=self.name, timeout_s=self._timeout, retries=self._retries, sleep=self._sleep
        )
        return parse_response(data, self.model)
