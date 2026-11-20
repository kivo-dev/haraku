"""Test doubles (stdlib only). Coordinates and places here are INVENTED for tests, not real data."""
from typing import Any, Optional

from app.ai.errors import ToolError
from app.ai.types import LLMResponse, ToolCall, Usage
from app.geo import haversine_km
from app.search_text import compact


def place(pid, fa, en, cat, lat=None, lng=None, verified=True, summary_fa="", summary_en=""):
    return {
        "id": pid, "category": cat, "name": {"fa": fa, "en": en}, "area": {"fa": "ماکو", "en": "Maku"},
        "summary": {"fa": summary_fa or fa, "en": summary_en or en}, "lat": lat, "lng": lng, "rating": None,
        "distanceKm": None, "featured": False, "image": None, "images": [], "reason": None, "verified": verified,
    }


PLACES = [
    place("qareh-kelisa", "قره‌کلیسا", "Qareh Kelisa", "history", 39.00, 44.00),
    place("maku-castle", "قلعه ماکو", "Maku Castle", "history", 39.02, 44.02, verified=False),
    place("waterfall", "آبشار نمونه", "Sample Waterfall", "nature", 39.10, 44.20),
    place("no-coords", "جای بدون مختصات", "No Coords Place", "nature"),
]


class FakeData:
    def __init__(self, places=None, route=None, fail_search=False):
        self.places = places if places is not None else PLACES
        self._route = route  # dict | ToolError | callable | None (default result)
        self.fail_search = fail_search
        self.route_calls = 0
        self.search_calls: list[dict] = []

    async def search_places(self, *, query, category, limit, lat=None, lng=None, radius_km=None):
        self.search_calls.append({"query": query, "category": category, "lat": lat})
        if self.fail_search:
            raise RuntimeError("database down")
        rows = [dict(p) for p in self.places]
        if category:
            rows = [p for p in rows if p["category"] == category]
        if query:
            q = compact(query)
            rows = [p for p in rows if q in compact(p["name"]["fa"] + p["name"]["en"] + p["summary"]["fa"] + p["summary"]["en"])]
        if lat is not None:
            rows = [p for p in rows if p["lat"] is not None]
            for p in rows:
                p["distanceKm"] = round(haversine_km(lat, lng, p["lat"], p["lng"]), 1)
            rows = [p for p in rows if radius_km is None or p["distanceKm"] <= radius_km]
            rows.sort(key=lambda p: p["distanceKm"])
        return rows[:limit], len(rows)

    async def get_place(self, place_id):
        return next((dict(p) for p in self.places if p["id"] == place_id), None)

    async def list_categories(self):
        return [{"key": "history", "title": {"fa": "تاریخی", "en": "Historical"}}, {"key": "nature", "title": {"fa": "طبیعت", "en": "Nature"}}]

    async def search_opportunities(self, *, query, sector, limit):
        return [{"id": "o1", "sector": "trade", "title": {"fa": "فرصت", "en": "Opportunity"}, "summary": {"fa": "x", "en": "y"}, "verified": False}][:limit]

    async def route(self, origin, destination, mode):
        self.route_calls += 1
        if isinstance(self._route, ToolError):
            raise self._route
        if mode != "car":
            raise ToolError("mode_unsupported", "Only driving")
        if callable(self._route):
            return self._route(origin, destination)
        return self._route or {"provider": "fake", "mode": "car", "distance_m": 12000, "duration_s": 900, "geometry": "abc"}


class ScriptedProvider:
    """Returns the scripted items in order. An item may be an LLMResponse, an Exception (raised) or a callable(messages)->LLMResponse."""

    name, model = "scripted", "scripted-1"

    def __init__(self, script):
        self.script, self.calls = list(script), []

    async def complete(self, system, messages, tools):
        self.calls.append({"system": system, "messages": list(messages), "tools": [t.name for t in tools]})
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item(messages) if callable(item) else item


def say(text, tin=10, tout=5):
    return LLMResponse(text, [], Usage(tin, tout))


def call(name, args, cid="c1", text=""):
    return LLMResponse(text, [ToolCall(cid, name, args)], Usage(10, 5))
