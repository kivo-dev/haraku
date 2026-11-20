"""Conversation manager + tool-calling loop. Provider-independent: talks only to LLMProvider and ToolRegistry."""
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from ..search_text import compact
from .data import TourismData
from .errors import AIError, InvalidInput
from .language import detect_language
from .memory import ConversationStore
from .prompts import FALLBACK, build_system_prompt
from .tools import Collected, ToolContext, ToolOutcome, ToolRegistry, _error_outcome, search_places
from .types import Message, Usage

log = logging.getLogger("harako.ai")
MAX_MESSAGE_CHARS = 1000
MAX_CALLS_PER_ROUND = 4


@dataclass
class AssistantRequest:
    message: str
    request_id: str
    conversation_id: Optional[str] = None
    language: Optional[str] = None
    location: Optional[tuple[float, float]] = None
    user_id: Optional[str] = None


@dataclass
class AssistantResult:
    conversation_id: str
    reply: str
    language: str
    request_id: str
    places: list[dict] = field(default_factory=list)
    routes: list[dict] = field(default_factory=list)
    itinerary: Optional[dict] = None
    degraded: bool = False
    error_code: Optional[str] = None
    conversation_reset: bool = False
    usage: dict[str, int] = field(default_factory=dict)
    tools: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: int = 0


def mentioned_places(text: str, places: dict[str, dict]) -> list[dict]:
    """Cards only for places the answer actually names (Persian or English name), so the UI never shows
    a record the text does not talk about, and never a record the tools did not return."""
    body = compact(text)
    out = []
    for p in places.values():
        for lang in ("fa", "en"):
            n = compact((p.get("name") or {}).get(lang, ""))
            if len(n) >= 3 and n in body:
                out.append(p)
                break
    return out


class Assistant:
    def __init__(self, provider, registry: ToolRegistry, store: ConversationStore, *, max_rounds: int = 5, route_budget: int = 4):
        self.provider, self.registry, self.store = provider, registry, store
        self.max_rounds, self.route_budget = max_rounds, route_budget

    async def chat(self, req: AssistantRequest, data: TourismData) -> AssistantResult:
        t0 = time.perf_counter()
        msg = (req.message or "").strip()
        if not msg:
            raise InvalidInput("Empty message")
        if len(msg) > MAX_MESSAGE_CHARS:
            raise InvalidInput(f"Message longer than {MAX_MESSAGE_CHARS} characters")

        conv = self.store.get(req.conversation_id, req.user_id)
        reset = bool(req.conversation_id) and conv is None  # unknown / expired / not yours: indistinguishable on purpose
        if conv is None:
            conv = self.store.create(req.user_id)
        language = req.language or detect_language(msg, default=conv.state.get("language", "fa"))
        conv.state["language"] = language

        ctx = ToolContext(data=data, language=language, location=req.location, user_id=req.user_id, route_budget=self.route_budget)
        result = AssistantResult(conversation_id=conv.id, reply="", language=language, request_id=req.request_id, conversation_reset=reset)
        usage = Usage()

        if self.provider is None:
            await self._degrade(result, ctx, msg, "ai_not_configured")
        else:
            try:
                turn = await self._run(conv, msg, ctx, language, usage, result)
            except AIError as exc:
                log.warning("assistant_degraded rid=%s code=%s", req.request_id, exc.code)
                await self._degrade(result, ctx, msg, exc.code)
            else:
                self.store.add_turn(conv, turn)

        result.usage = {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}
        result.latency_ms = int((time.perf_counter() - t0) * 1000)
        log.info(
            "assistant rid=%s lang=%s degraded=%s code=%s tools=%d tokens_in=%d tokens_out=%d ms=%d",
            req.request_id, language, result.degraded, result.error_code, len(result.tools),
            usage.input_tokens, usage.output_tokens, result.latency_ms,
        )  # no message text, no keys
        return result

    async def _run(self, conv, msg: str, ctx: ToolContext, language: str, usage: Usage, result: AssistantResult) -> list[Message]:
        system = build_system_prompt(language, ctx.location is not None)
        history = self.store.messages(conv)
        turn: list[Message] = [Message("user", msg)]
        final = ""
        for round_no in range(self.max_rounds + 1):
            last = round_no == self.max_rounds  # final round: no tools offered, the model must answer
            resp = await self.provider.complete(system, history + turn, [] if last else self.registry.specs_for(ctx))
            usage.add(resp.usage)
            if resp.tool_calls and not last:
                turn.append(Message("assistant", resp.text, resp.tool_calls))
                for i, call in enumerate(resp.tool_calls):  # EVERY call gets a result (providers require it)
                    if i >= MAX_CALLS_PER_ROUND:
                        out: ToolOutcome = _error_outcome(call.name[:40], "too_many_tool_calls", "Too many tool calls at once.")
                    else:
                        out = await self.registry.execute(call, ctx)
                    result.tools.append({"name": out.name, "ok": out.ok, "ms": out.ms, "error": out.error_code})
                    turn.append(Message("tool", out.content, tool_call_id=call.id))
                continue
            final = resp.text.strip()
            break
        if not final:
            final = FALLBACK[language]["empty"]
            result.degraded, result.error_code = True, "empty_answer"
        turn.append(Message("assistant", final))
        result.reply = final
        result.places = mentioned_places(final, ctx.collected.places)
        result.routes = ctx.collected.routes
        result.itinerary = ctx.collected.itinerary
        return turn

    async def _degrade(self, result: AssistantResult, ctx: ToolContext, msg: str, code: str) -> None:
        """AI unavailable: the app keeps working. Plain HARAKO search results instead of a smart answer."""
        result.degraded, result.error_code = True, code
        texts = FALLBACK[result.language]
        result.places, result.routes, result.itinerary = [], [], None
        ctx.collected = Collected()  # drop anything a half-finished smart run collected
        try:
            await search_places(ctx, query=msg[:100])  # same code path as the tool (incl. word-by-word retry)
        except Exception:
            log.exception("fallback_search_failed rid=%s", result.request_id)
        found = list(ctx.collected.places.values())[:5]
        if found:
            result.reply = texts["results"].format(q=msg[:60])
            result.places = found
        else:
            result.reply = texts["none"]
