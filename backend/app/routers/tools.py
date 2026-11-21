"""AI-assistant tool endpoints  (/v1/tools/*).

The AI service calls these server-to-server; the LLM itself never touches the database or any provider
key. Auth: header `X-Tools-Key` must equal TOOLS_API_KEY (when set; required in production).
`GET /v1/tools/manifest` lists every tool with inputs and its availability, so the AI developer can
generate tool definitions from it.
"""
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..constants import SAMPLE_SOURCE, VERIFIED
from ..db import get_db
from ..mappers import opportunity_to_out
from ..models import Category, Opportunity, Place
from ..providers.base import GeocodingProvider, ProviderDisabled, ProviderError, RoutingProvider
from ..providers.registry import capability_status, get_geocoding_provider, get_routing_provider
from ..ratelimit import check_tools_paid_limit
from ..routers.routes import resolve_destination
from ..schemas import CategoryOut, Localized, OpportunityList
from ..schemas_tools import Coordinates, ExternalPlace, GeocodeOut, ReverseGeocodeOut, ToolPlace, ToolPlaceList, ToolRoute
from ..search_text import query_keys
from ..services.discovery import search_places as discovery_search
from ..services.discovery import visible_opportunities_stmt, visible_places_stmt


def require_tools_access(x_tools_key: Optional[str] = Header(None)) -> None:
    s = get_settings()
    if not s.tools_enabled:
        raise HTTPException(404, "Not found")
    if s.tools_api_key and not secrets.compare_digest((x_tools_key or "").encode(), s.tools_api_key.encode()):
        raise HTTPException(401, "Missing or invalid X-Tools-Key")


router = APIRouter(prefix="/tools", dependencies=[Depends(require_tools_access)])


def _loc(fa: Optional[str], en: Optional[str]) -> Localized:
    fa, en = fa or "", en or ""
    return Localized(fa=fa or en, en=en or fa)


def place_to_tool(p: Place, distance_km: Optional[float] = None) -> ToolPlace:
    return ToolPlace(
        id=p.id,
        category=p.category_key,
        name=_loc(p.name_fa, p.name_en),
        area=_loc(p.area_fa, p.area_en),
        summary=_loc(p.summary_fa, p.summary_en),
        coordinates=Coordinates(lat=p.lat, lng=p.lng) if p.lat is not None and p.lng is not None else None,
        distance_km=round(distance_km, 2) if distance_km is not None else None,
        rating=p.rating,
        verified=p.verification == VERIFIED,
        verification_status=p.verification,
        last_verified_at=p.last_verified_at,
        record_source=p.source,
        is_sample=p.source == SAMPLE_SOURCE,
    )


def _pair(lat: Optional[float], lng: Optional[float]) -> None:
    if (lat is None) != (lng is None):
        raise HTTPException(422, "lat and lng must be given together")


@router.get("/search_places", response_model=ToolPlaceList)
def tool_search_places(
    q: Optional[str] = Query(None, max_length=100),
    category: Optional[str] = None,
    lat: Optional[float] = Query(None, ge=-90, le=90),
    lng: Optional[float] = Query(None, ge=-180, le=180),
    radius_km: Optional[float] = Query(None, gt=0, le=500),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    _pair(lat, lng)
    if radius_km is not None and lat is None:
        raise HTTPException(422, "radius_km needs lat and lng")
    page, total = discovery_search(db, category=category, q=q, lat=lat, lng=lng, radius_km=radius_km, limit=limit, offset=offset)
    return ToolPlaceList(items=[place_to_tool(p, d) for p, d in page], total=total, limit=limit, offset=offset)


@router.get("/nearby_places", response_model=ToolPlaceList)
def tool_nearby_places(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(25, gt=0, le=200),
    category: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    page, total = discovery_search(db, category=category, lat=lat, lng=lng, radius_km=radius_km, limit=limit)
    return ToolPlaceList(items=[place_to_tool(p, d) for p, d in page], total=total, limit=limit, offset=0)


@router.get("/get_place/{place_id}", response_model=ToolPlace)
def tool_get_place(place_id: str, db: Session = Depends(get_db)):
    p = db.scalar(visible_places_stmt().options(selectinload(Place.images)).where(Place.id == place_id))
    if p is None:
        raise HTTPException(404, "Place not found")
    return place_to_tool(p)


@router.get("/get_categories", response_model=list[CategoryOut])
def tool_get_categories(db: Session = Depends(get_db)):
    rows = db.scalars(select(Category).order_by(Category.sort, Category.key)).all()
    return [CategoryOut(key=c.key, title=Localized(fa=c.title_fa, en=c.title_en)) for c in rows]


@router.get("/search_opportunities", response_model=OpportunityList)
def tool_search_opportunities(
    sector: Optional[str] = Query(None, description="trade | industry | agriculture | tourism"),
    q: Optional[str] = Query(None, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    stmt = visible_opportunities_stmt()
    if sector:
        stmt = stmt.where(Opportunity.sector == sector)
    keys = query_keys(q)
    if keys:
        n, c = keys
        stmt = stmt.where(or_(Opportunity.search_text.contains(n, autoescape=True), Opportunity.search_compact.contains(c, autoescape=True)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Opportunity.sector, Opportunity.title_fa, Opportunity.id).limit(limit)).all()
    return OpportunityList(items=[opportunity_to_out(o) for o in rows], total=total)


@router.get("/get_route", response_model=ToolRoute, dependencies=[Depends(check_tools_paid_limit)])
async def tool_get_route(
    from_lat: float = Query(..., ge=-90, le=90),
    from_lng: float = Query(..., ge=-180, le=180),
    to_place: Optional[str] = None,
    to_lat: Optional[float] = Query(None, ge=-90, le=90),
    to_lng: Optional[float] = Query(None, ge=-180, le=180),
    mode: str = Query("car", pattern="^car$"),
    db: Session = Depends(get_db),
    provider: RoutingProvider = Depends(get_routing_provider),
):
    dest = resolve_destination(db, to_place, to_lat, to_lng)
    try:
        r = await provider.route((from_lat, from_lng), dest, mode)
    except ProviderDisabled:
        raise HTTPException(503, "Routing is not configured on the server")
    except ProviderError as exc:
        raise HTTPException(502, str(exc))
    state = next((c["state"] for c in capability_status() if c["capability"] == "routing_car"), "unverified")
    return ToolRoute(
        provider=r.provider,
        provider_status=state,
        mode=r.mode,
        distance_m=r.distance_m,
        duration_s=r.duration_s,
        geometry=r.geometry,
        destination=Coordinates(lat=dest[0], lng=dest[1]),
        destination_place_id=to_place or None,
    )


@router.get("/geocode", response_model=GeocodeOut, dependencies=[Depends(check_tools_paid_limit)])
async def tool_geocode(
    q: str = Query(..., min_length=2, max_length=200),
    provider: GeocodingProvider = Depends(get_geocoding_provider),
):
    res = await provider.geocode(q, None)
    return GeocodeOut(query=q, provider=res[0].provider if res else "none",
                      results=[ExternalPlace(label=r.label, lat=r.lat, lng=r.lng, provider=r.provider) for r in res])


@router.get("/reverse_geocode", response_model=ReverseGeocodeOut, dependencies=[Depends(check_tools_paid_limit)])
async def tool_reverse_geocode(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    provider: GeocodingProvider = Depends(get_geocoding_provider),
):
    r = await provider.reverse(lat, lng)
    if r is None:
        return ReverseGeocodeOut(lat=lat, lng=lng, provider="none")
    return ReverseGeocodeOut(lat=lat, lng=lng, provider=r.provider, label=r.label, components=r.components)


_TOOLS = [
    ("search_places", "Search HARAKO's verified tourism database by text, category and optional position.", "/v1/tools/search_places",
     {"q": "string?", "category": "string?", "lat": "number?", "lng": "number?", "radius_km": "number? (needs lat,lng)", "limit": "int 1-50", "offset": "int"}, "database"),
    ("nearby_places", "HARAKO places around a coordinate, nearest first.", "/v1/tools/nearby_places",
     {"lat": "number", "lng": "number", "radius_km": "number (default 25, max 200)", "category": "string?", "limit": "int 1-50"}, "database"),
    ("get_place", "One HARAKO place by id.", "/v1/tools/get_place/{place_id}", {"place_id": "string (path)"}, "database"),
    ("get_categories", "All place categories.", "/v1/tools/get_categories", {}, "database"),
    ("search_opportunities", "Search economic opportunities.", "/v1/tools/search_opportunities",
     {"sector": "trade|industry|agriculture|tourism ?", "q": "string?", "limit": "int 1-50"}, "database"),
    ("get_route", "Driving route to a HARAKO place or coordinates (provider adapter UNVERIFIED).", "/v1/tools/get_route",
     {"from_lat": "number", "from_lng": "number", "to_place": "string?", "to_lat": "number?", "to_lng": "number?", "mode": "car"}, "routing_car"),
    ("geocode", "Address/text to coordinates (external result, never a verified HARAKO place).", "/v1/tools/geocode", {"q": "string"}, "geocode"),
    ("reverse_geocode", "Coordinates to an address (external result).", "/v1/tools/reverse_geocode", {"lat": "number", "lng": "number"}, "reverse_geocode"),
]


@router.get("/manifest")
def manifest():
    status = {c["capability"]: c["state"] for c in capability_status()}
    return {
        "version": 1,
        "auth": "header X-Tools-Key (when TOOLS_API_KEY is set)",
        "rules": [
            "data_source 'harako_db' = HARAKO's own records; 'external' = map-provider results, never verified.",
            "Null means unknown. Do not invent ratings, hours, prices or distances.",
            "is_sample=true records are placeholders, never present them as real facts.",
            "HTTP 501 code=provider_not_implemented means the capability is not available yet.",
        ],
        "tools": [
            {"name": n, "description": d, "method": "GET", "path": path, "inputs": i,
             "state": "verified" if dep == "database" else status.get(dep, "pending")}
            for n, d, path, i, dep in _TOOLS
        ],
    }
