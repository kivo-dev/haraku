"""HTTP layer of the assistant.  POST /v1/assistant/chat   GET /v1/assistant/status"""
import logging
import re
import uuid
from functools import lru_cache
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..ratelimit import check_ai_limit
from ..schemas import Localized, PlaceOut
from .data import DbTourismData
from .errors import AIError, InvalidInput
from .llm import build_provider
from .memory import ConversationStore
from .orchestrator import Assistant, AssistantRequest
from .tools import default_registry

log = logging.getLogger("harako.ai")
router = APIRouter()
_RID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


@lru_cache
def get_assistant() -> Assistant:
    s = get_settings()
    try:
        provider = build_provider(s)
    except AIError as exc:  # half-configured: assistant runs in degraded mode, the app still starts
        log.error("ai_provider_misconfigured code=%s detail=%s", exc.code, exc)
        provider = None
    store = ConversationStore(ttl_s=s.ai_conversation_ttl_s)
    return Assistant(provider, default_registry(), store, max_rounds=s.ai_max_tool_rounds, route_budget=s.ai_route_calls_per_request)


class LocationIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    conversation_id: Optional[str] = Field(None, max_length=64)
    language: Optional[Literal["fa", "en"]] = None
    location: Optional[LocationIn] = None  # only if the user granted permission


class PointOut(BaseModel):
    id: Optional[str] = None
    name: Optional[Localized] = None
    lat: float
    lng: float


class RouteCardOut(BaseModel):
    provider: str
    mode: str
    distance_m: int
    duration_s: int
    geometry: Optional[str] = None  # encoded polyline exactly as the provider returned it
    origin: PointOut
    destination: PointOut


class ChatOut(BaseModel):
    conversation_id: str
    reply: str
    language: str
    places: list[PlaceOut] = []  # real HARAKO records the reply talks about (render as cards)
    routes: list[RouteCardOut] = []
    itinerary: Optional[dict[str, Any]] = None
    degraded: bool = False  # true = AI unavailable/failed; reply is a plain-search fallback
    error_code: Optional[str] = None
    conversation_reset: bool = False  # the given conversation_id was unknown/expired: a new one started
    request_id: str


@router.post("/assistant/chat", response_model=ChatOut, dependencies=[Depends(check_ai_limit)])
async def chat(body: ChatIn, db: Session = Depends(get_db), x_request_id: Optional[str] = Header(None)):
    rid = x_request_id if x_request_id and _RID.match(x_request_id) else uuid.uuid4().hex[:16]
    req = AssistantRequest(
        message=body.message, request_id=rid, conversation_id=body.conversation_id, language=body.language,
        location=(body.location.lat, body.location.lng) if body.location else None,
        user_id=None,  # anonymous until HARAKO has accounts; pass the signed-in user's id here later
    )
    try:
        r = await get_assistant().chat(req, DbTourismData(db, get_settings()))
    except InvalidInput as exc:
        raise HTTPException(422, str(exc))
    return ChatOut(
        conversation_id=r.conversation_id, reply=r.reply, language=r.language,
        places=[PlaceOut.model_validate(p) for p in r.places],
        routes=[RouteCardOut.model_validate(x) for x in r.routes],
        itinerary=r.itinerary, degraded=r.degraded, error_code=r.error_code,
        conversation_reset=r.conversation_reset, request_id=r.request_id,
    )


@router.get("/assistant/status")
def status():
    a = get_assistant()
    return {"enabled": a.provider is not None, "provider": getattr(a.provider, "name", None), "model": getattr(a.provider, "model", None)}
