"""Provider interface + shared HTTP/retry helper.

Business code only knows `LLMProvider`. A new vendor = one new file implementing `complete()`;
nothing else changes. Errors are normalised to the AIError family (no vendor text, no keys)."""
import asyncio
import logging
from typing import Any, Awaitable, Callable, Optional, Protocol

from ..errors import LLMRejected, LLMUnavailable, TransportError
from ..types import LLMResponse, Message, ToolSpec

log = logging.getLogger("harako.ai.llm")

# (url, headers, json_body, timeout_s) -> (status_code, parsed_json_or_empty_dict)
Poster = Callable[[str, dict[str, str], dict[str, Any], float], Awaitable[tuple[int, dict[str, Any]]]]

TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504, 529}


class LLMProvider(Protocol):
    name: str
    model: str

    async def complete(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMResponse: ...


async def httpx_post(url: str, headers: dict[str, str], body: dict[str, Any], timeout_s: float) -> tuple[int, dict[str, Any]]:
    import httpx  # imported lazily: the AI core stays importable without it

    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            res = await client.post(url, headers=headers, json=body)
    except httpx.HTTPError as exc:  # timeouts and transport errors; message deliberately not forwarded
        raise TransportError(type(exc).__name__) from exc
    try:
        data = res.json()
    except ValueError:
        data = {}
    return res.status_code, data if isinstance(data, dict) else {}


async def post_with_retry(
    post: Poster,
    url: str,
    headers: dict[str, str],
    body: dict[str, Any],
    *,
    provider: str,
    timeout_s: float,
    retries: int = 2,
    sleep: Optional[Callable[[float], Awaitable[None]]] = None,
) -> dict[str, Any]:
    sleep = sleep or asyncio.sleep
    attempt = 0
    while True:
        status: Optional[int] = None
        try:
            status, data = await post(url, headers, body, timeout_s)
        except (TransportError, asyncio.TimeoutError):
            pass  # transient: handled below
        else:
            if status == 200:
                return data
            if status in (401, 403):
                log.error("llm_auth_failed provider=%s status=%s", provider, status)
                raise LLMRejected("The AI provider rejected the credentials")
            if status not in TRANSIENT_STATUS:
                log.error("llm_request_rejected provider=%s status=%s", provider, status)
                raise LLMRejected("The AI provider rejected the request")
        if attempt >= retries:
            log.error("llm_unavailable provider=%s status=%s attempts=%d", provider, status, attempt + 1)
            raise LLMUnavailable("The AI provider is not available right now")
        await sleep(0.5 * (2**attempt))
        attempt += 1
