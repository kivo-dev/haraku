from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..providers.base import LatLng, ProviderDisabled, ProviderError, RoutingProvider
from ..providers.registry import get_routing_provider
from ..ratelimit import check_route_limit
from ..schemas import RouteOut
from ..services.discovery import visible_places_stmt
from ..models import Place

router = APIRouter()


def resolve_destination(db: Session, to_place: Optional[str], to_lat: Optional[float], to_lng: Optional[float]) -> LatLng:
    """A HARAKO place id, or coordinates. Shared with the AI tool endpoint."""
    if to_place:
        place = db.scalar(visible_places_stmt().where(Place.id == to_place))
        if place is None:
            raise HTTPException(404, "Place not found")
        if place.lat is None or place.lng is None:
            raise HTTPException(422, "This place has no coordinates yet")
        return (place.lat, place.lng)
    if to_lat is not None and to_lng is not None:
        return (to_lat, to_lng)
    raise HTTPException(422, "Give to_place or both to_lat and to_lng")


@router.get("/route", response_model=RouteOut, dependencies=[Depends(check_route_limit)])
async def get_route(
    from_lat: float = Query(..., ge=-90, le=90),
    from_lng: float = Query(..., ge=-180, le=180),
    to_place: Optional[str] = Query(None, description="id of a HARAKO place"),
    to_lat: Optional[float] = Query(None, ge=-90, le=90),
    to_lng: Optional[float] = Query(None, ge=-180, le=180),
    mode: str = Query("car", pattern="^car$"),
    db: Session = Depends(get_db),
    provider: RoutingProvider = Depends(get_routing_provider),
):
    """Route from the user to a place (by id) or to coordinates. Needs the Neshan key on the server.
    NOTE: the Neshan routing adapter is still UNVERIFIED (see app/services/neshan.py)."""
    dest = resolve_destination(db, to_place, to_lat, to_lng)
    try:
        r = await provider.route((from_lat, from_lng), dest, mode)
    except ProviderDisabled:
        raise HTTPException(503, "Routing is not configured on the server")
    except ProviderError as exc:
        raise HTTPException(502, str(exc))
    return RouteOut(provider=r.provider, mode=r.mode, distance_m=r.distance_m, duration_s=r.duration_s, geometry=r.geometry)
