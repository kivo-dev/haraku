"""The tools the model may call. Every call is: authorised -> validated -> time-limited -> logged.
Results are plain JSON for the model; the full records for the UI (cards, routes) are collected on the side
so the frontend only ever renders real HARAKO records."""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from ..search_text import normalize
from .data import TourismData
from .errors import ToolError
from .itinerary import MAX_STOPS, Stop, best_order, summarize
from .types import ToolCall, ToolSpec
from .validation import validate_args

log = logging.getLogger("harako.ai.tools")
MAX_RESULTS = 10


@dataclass
class Collected:
    places: dict[str, dict] = field(default_factory=dict)  # id -> full record (cards)
    routes: list[dict] = field(default_factory=list)
    itinerary: Optional[dict] = None


@dataclass
class ToolContext:
    data: TourismData
    language: str = "fa"
    location: Optional[tuple[float, float]] = None  # user position, only if the client sent it
    user_id: Optional[str] = None  # None = anonymous
    route_budget: int = 4  # provider calls allowed in ONE chat request (routing costs quota)
    collected: Collected = field(default_factory=Collected)


@dataclass
class ToolOutcome:
    name: str
    ok: bool
    content: str  # JSON string handed back to the model
    ms: int = 0
    error_code: Optional[str] = None


Handler = Callable[..., Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class Tool:
    spec: ToolSpec
    handler: Handler
    requires_auth: bool = False
    timeout_s: float = 10.0


def _dump(payload: dict[str, Any], limit: int = 6000) -> str:
    s = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(s) > limit:
        s = json.dumps({"ok": False, "error": {"code": "result_too_large", "message": "Result too large; ask for fewer items."}})
    return s


def _error_outcome(name: str, code: str, message: str, ms: int = 0) -> ToolOutcome:
    return ToolOutcome(name, False, _dump({"ok": False, "error": {"code": code, "message": message}}), ms, code)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.spec.name] = tool

    def specs_for(self, ctx: ToolContext) -> list[ToolSpec]:
        """The model only SEES tools this user may use (anonymous users never see account tools)."""
        return [t.spec for t in self._tools.values() if not t.requires_auth or ctx.user_id is not None]

    async def execute(self, call: ToolCall, ctx: ToolContext) -> ToolOutcome:
        t0 = time.perf_counter()
        tool = self._tools.get(call.name)
        if tool is None:
            return _error_outcome(call.name[:40], "unknown_tool", "No such tool.")
        if tool.requires_auth and ctx.user_id is None:  # second check, in case the model asks for a hidden tool
            return _error_outcome(call.name, "authentication_required", "This action needs a signed-in user.")
        code: Optional[str] = None
        try:
            args = validate_args(call.arguments, tool.spec.parameters)
            data = await asyncio.wait_for(tool.handler(ctx, **args), tool.timeout_s)
            out = ToolOutcome(call.name, True, _dump({"ok": True, "data": data}))
        except ToolError as exc:
            code = exc.code
            out = _error_outcome(call.name, exc.code, exc.message)
        except asyncio.TimeoutError:
            code = "tool_timeout"
            out = _error_outcome(call.name, code, "The tool took too long.")
        except Exception:  # never leak internals to the model or the client
            log.exception("tool_failed name=%s", call.name)
            code = "tool_failed"
            out = _error_outcome(call.name, code, "The tool failed.")
        out.ms = int((time.perf_counter() - t0) * 1000)
        log.info("tool name=%s ok=%s code=%s ms=%d", call.name, out.ok, code, out.ms)
        return out


# ---------------------------------------------------------------- helpers

def _clip(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def _compact_place(p: dict, language: str) -> dict:
    other = "en" if language == "fa" else "fa"
    summary = (p.get("summary") or {}).get(language) or (p.get("summary") or {}).get(other) or ""
    out = {
        "id": p["id"],
        "name_fa": (p.get("name") or {}).get("fa", ""),
        "name_en": (p.get("name") or {}).get("en", ""),
        "category": p.get("category"),
        "area": (p.get("area") or {}).get(language, ""),
        "summary": _clip(summary, 300),
        "lat": p.get("lat"),
        "lng": p.get("lng"),
        "verified": bool(p.get("verified")),
        "rating": p.get("rating"),
    }
    if p.get("distanceKm") is not None:
        out["distance_km"] = p["distanceKm"]
        out["distance_type"] = "straight_line"  # NOT a driving distance
    return out


def _collect(ctx: ToolContext, places: list[dict]) -> list[dict]:
    for p in places:
        ctx.collected.places[p["id"]] = p
    return [_compact_place(p, ctx.language) for p in places]


def _tokens(q: str) -> list[str]:
    return [t for t in normalize(q).split() if len(t) >= 3][:4]


async def _resolve_point(ctx: ToolContext, place_id: Optional[str], lat: Optional[float], lng: Optional[float]) -> Optional[dict]:
    if place_id:
        p = await ctx.data.get_place(place_id)
        if p is None:
            raise ToolError("place_not_found", f"No published place with id '{place_id}'.")
        if p.get("lat") is None or p.get("lng") is None:
            raise ToolError("place_has_no_coordinates", f"'{place_id}' has no coordinates yet, so it cannot be routed to.")
        ctx.collected.places[p["id"]] = p
        return {"id": p["id"], "name": p.get("name"), "lat": p["lat"], "lng": p["lng"]}
    if (lat is None) != (lng is None):
        raise ToolError("invalid_arguments", "latitude and longitude must be given together")
    if lat is not None:
        return {"id": None, "name": None, "lat": lat, "lng": lng}
    return None


def _spend_route(ctx: ToolContext) -> None:
    if ctx.route_budget <= 0:
        raise ToolError("route_budget_exceeded", "Too many route lookups in one request. Answer with what you already have.")
    ctx.route_budget -= 1


async def _route_leg(ctx: ToolContext, a: dict, b: dict, mode: str) -> dict:
    _spend_route(ctx)
    r = await ctx.data.route((a["lat"], a["lng"]), (b["lat"], b["lng"]), mode)
    ctx.collected.routes.append({**r, "origin": a, "destination": b})
    return r


# ---------------------------------------------------------------- handlers

async def search_places(ctx: ToolContext, query: Optional[str] = None, category: Optional[str] = None, limit: int = 5) -> dict:
    if not query and not category:
        raise ToolError("invalid_arguments", "give a query and/or a category")
    places, total = await ctx.data.search_places(query=query, category=category, limit=limit)
    if not places and query and len(_tokens(query)) > 1:  # "historical places Maku" -> try the words one by one
        seen: dict[str, dict] = {}
        for tok in _tokens(query):
            found, _ = await ctx.data.search_places(query=tok, category=category, limit=limit)
            for p in found:
                seen.setdefault(p["id"], p)
        places = list(seen.values())[:limit]
        total = len(seen)
    out: dict[str, Any] = {"count": len(places), "total_matches": total, "places": _collect(ctx, places)}
    if not places:
        out["note"] = "No published HARAKO place matched. Say so honestly; do not invent places."
    return out


async def nearby_places(
    ctx: ToolContext, latitude: Optional[float] = None, longitude: Optional[float] = None,
    radius_km: float = 25, category: Optional[str] = None, limit: int = 5,
) -> dict:
    if (latitude is None) != (longitude is None):
        raise ToolError("invalid_arguments", "latitude and longitude must be given together")
    if latitude is None:
        if ctx.location is None:
            raise ToolError("location_required", "The user's location is not available. Ask them to share it or to name a starting place.")
        latitude, longitude = ctx.location
    places, total = await ctx.data.search_places(query=None, category=category, limit=limit, lat=latitude, lng=longitude, radius_km=radius_km)
    out: dict[str, Any] = {"count": len(places), "total_matches": total, "radius_km": radius_km, "places": _collect(ctx, places)}
    if not places:
        out["note"] = "No published place with coordinates inside this radius."
    return out


async def get_place(ctx: ToolContext, place_id: str) -> dict:
    p = await ctx.data.get_place(place_id)
    if p is None:
        raise ToolError("place_not_found", f"No published place with id '{place_id}'.")
    ctx.collected.places[p["id"]] = p
    d = _compact_place(p, ctx.language)
    d["has_coordinates"] = p.get("lat") is not None and p.get("lng") is not None
    d["summary"] = (p.get("summary") or {}).get(ctx.language) or (p.get("summary") or {}).get("fa", "")
    return {"place": d}


async def get_categories(ctx: ToolContext) -> dict:
    cats = await ctx.data.list_categories()
    return {"categories": [{"key": c["key"], "title_fa": c["title"]["fa"], "title_en": c["title"]["en"]} for c in cats]}


async def search_opportunities(ctx: ToolContext, query: Optional[str] = None, sector: Optional[str] = None, limit: int = 5) -> dict:
    items = await ctx.data.search_opportunities(query=query, sector=sector, limit=limit)
    lang = ctx.language
    return {
        "count": len(items),
        "opportunities": [
            {"id": o["id"], "sector": o["sector"], "title": (o.get("title") or {}).get(lang, ""),
             "summary": _clip((o.get("summary") or {}).get(lang, ""), 300), "verified": bool(o.get("verified"))}
            for o in items
        ],
    }


async def get_route(
    ctx: ToolContext, destination_place_id: Optional[str] = None, destination_lat: Optional[float] = None,
    destination_lng: Optional[float] = None, origin_place_id: Optional[str] = None, origin_lat: Optional[float] = None,
    origin_lng: Optional[float] = None, mode: str = "car",
) -> dict:
    dest = await _resolve_point(ctx, destination_place_id, destination_lat, destination_lng)
    if dest is None:
        raise ToolError("destination_required", "Give destination_place_id or destination_lat+destination_lng.")
    origin = await _resolve_point(ctx, origin_place_id, origin_lat, origin_lng)
    if origin is None and ctx.location is not None:
        origin = {"id": None, "name": None, "lat": ctx.location[0], "lng": ctx.location[1]}
    if origin is None:
        raise ToolError("origin_required", "The user's location is not available. Ask them to share it or to name a starting place.")
    r = await _route_leg(ctx, origin, dest, mode)
    return {
        "mode": r["mode"], "provider": r["provider"],
        "distance_km": round(r["distance_m"] / 1000, 1), "duration_min": round(r["duration_s"] / 60),
        "origin_place_id": origin["id"], "destination_place_id": dest["id"],
    }


async def plan_itinerary(
    ctx: ToolContext, place_ids: list, start_lat: Optional[float] = None, start_lng: Optional[float] = None,
    mode: str = "car", available_hours: Optional[float] = None,
) -> dict:
    if (start_lat is None) != (start_lng is None):
        raise ToolError("invalid_arguments", "start_lat and start_lng must be given together")
    start = (start_lat, start_lng) if start_lat is not None else ctx.location
    stops: list[Stop] = []
    skipped: list[dict] = []
    for pid in dict.fromkeys(place_ids):  # de-duplicated, order kept
        p = await ctx.data.get_place(pid)
        if p is None:
            skipped.append({"place_id": pid, "reason": "not_found"})
        elif p.get("lat") is None or p.get("lng") is None:
            skipped.append({"place_id": pid, "reason": "no_coordinates"})
        else:
            ctx.collected.places[p["id"]] = p
            stops.append(Stop(p["id"], (p.get("name") or {}).get(ctx.language) or p["id"], p["lat"], p["lng"]))
    if len(stops) < 2:
        raise ToolError("not_enough_stops", f"Need at least 2 places with coordinates; usable: {len(stops)}; skipped: {skipped}")
    ordered = best_order(start, stops)

    points: list[dict] = ([{"id": None, "name": None, "lat": start[0], "lng": start[1]}] if start else []) + [
        {"id": s.id, "name": s.name, "lat": s.lat, "lng": s.lng} for s in ordered
    ]
    legs: list[dict] = []
    warnings: list[str] = []
    for a, b in zip(points, points[1:]):
        leg: dict[str, Any] = {"from": a["id"] or "start", "to": b["id"]}
        try:
            r = await _route_leg(ctx, a, b, mode)
            leg.update(source="routing", distance_km=round(r["distance_m"] / 1000, 1), duration_min=round(r["duration_s"] / 60))
        except ToolError as exc:
            from ..geo import haversine_km

            leg.update(source="straight_line_estimate_only", distance_km=round(haversine_km(a["lat"], a["lng"], b["lat"], b["lng"]), 1), duration_min=None)
            warnings.append(f"{leg['from']}->{leg['to']}: no routed time ({exc.code})")
        legs.append(leg)
    summary = summarize(legs, available_hours)
    ctx.collected.itinerary = {"stops": [s.id for s in ordered], "legs": legs, **summary}
    notes = ["Visit durations are not in HARAKO's data: do not invent them.", "Straight-line legs have no travel time."]
    return {"ordered_place_ids": [s.id for s in ordered], "legs": legs, **summary, "skipped": skipped, "warnings": warnings, "notes": notes}


# ---------------------------------------------------------------- registry

def _obj(props: dict, required: Optional[list] = None) -> dict:
    return {"type": "object", "properties": props, "required": required or []}


_LAT = {"type": "number", "minimum": -90, "maximum": 90}
_LNG = {"type": "number", "minimum": -180, "maximum": 180}
_LIMIT = {"type": "integer", "minimum": 1, "maximum": MAX_RESULTS, "default": 5}
_MODE = {"type": "string", "enum": ["car", "walking", "bicycle"], "default": "car"}
_PID = {"type": "string", "minLength": 1, "maxLength": 80}


def default_registry() -> ToolRegistry:
    r = ToolRegistry()
    add = lambda name, desc, params, fn, t=10.0: r.register(Tool(ToolSpec(name, desc, params), fn, False, t))  # noqa: E731
    add("search_places",
        "Search HARAKO's published places by name/keywords and/or category. Use SHORT keywords (a place name or one word), "
        "not whole sentences; use `category` for kinds of places (call get_categories first if unsure of the keys).",
        _obj({"query": {"type": "string", "minLength": 1, "maxLength": 100}, "category": {"type": "string", "maxLength": 40}, "limit": _LIMIT}),
        search_places)
    add("nearby_places",
        "Places near a point, sorted by STRAIGHT-LINE distance. Without latitude/longitude it uses the user's shared location.",
        _obj({"latitude": _LAT, "longitude": _LNG, "radius_km": {"type": "number", "minimum": 1, "maximum": 200, "default": 25},
              "category": {"type": "string", "maxLength": 40}, "limit": _LIMIT}),
        nearby_places)
    add("get_place", "Full details of one place by id.", _obj({"place_id": _PID}, ["place_id"]), get_place)
    add("get_categories", "List place categories (keys and titles).", _obj({}), get_categories)
    add("search_opportunities", "Search regional economic opportunities (trade, industry, agriculture, tourism).",
        _obj({"query": {"type": "string", "minLength": 1, "maxLength": 100},
              "sector": {"type": "string", "enum": ["trade", "industry", "agriculture", "tourism"]}, "limit": _LIMIT}),
        search_opportunities)
    add("get_route",
        "Real route (distance and driving time) from the routing provider. Destination: a HARAKO place id or coordinates. "
        "Origin defaults to the user's shared location. Only mode 'car' works today.",
        _obj({"destination_place_id": _PID, "destination_lat": _LAT, "destination_lng": _LNG,
              "origin_place_id": _PID, "origin_lat": _LAT, "origin_lng": _LNG, "mode": _MODE}),
        get_route, 15.0)
    add("plan_itinerary",
        f"Order 2-{MAX_STOPS} HARAKO places into an efficient visiting sequence and measure each leg with the routing provider. "
        "Returns real travel times only; visit durations are unknown.",
        _obj({"place_ids": {"type": "array", "items": _PID, "minItems": 2, "maxItems": MAX_STOPS},
              "start_lat": _LAT, "start_lng": _LNG, "mode": _MODE,
              "available_hours": {"type": "number", "minimum": 0.5, "maximum": 48}}, ["place_ids"]),
        plan_itinerary, 30.0)
    return r
