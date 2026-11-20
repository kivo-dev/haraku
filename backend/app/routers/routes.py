from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import PUBLISHED, Place
from ..ratelimit import check_route_limit
from ..schemas import RouteOut
from ..services.neshan import NeshanRouting, ProviderDisabled, ProviderError

router = APIRouter()


@router.get("/route", response_model=RouteOut, dependencies=[Depends(check_route_limit)])
async def get_route(
    from_lat: float = Query(..., ge=-90, le=90),
    from_lng: float = Query(..., ge=-180, le=180),
    to_place: Optional[str] = Query(None, description="id of a HARAKO place"),
    to_lat: Optional[float] = Query(None, ge=-90, le=90),
    to_lng: Optional[float] = Query(None, ge=-180, le=180),
    mode: str = Query("car", pattern="^car$"),
    db: Session = Depends(get_db),
):
    """Route from the user to a place (by id) or to coordinates. Needs the Neshan key on the server."""
    if to_place:
        place = db.scalar(select(Place).where(Place.id == to_place, Place.status == PUBLISHED))
        if place is None:
            raise HTTPException(404, "Place not found")
        if place.lat is None or place.lng is None:
            raise HTTPException(422, "This place has no coordinates yet")
        dest = (place.lat, place.lng)
    elif to_lat is not None and to_lng is not None:
        dest = (to_lat, to_lng)
    else:
        raise HTTPException(422, "Give to_place or both to_lat and to_lng")

    settings = get_settings()
    provider = NeshanRouting(settings.neshan_service_key, settings.neshan_timeout_s)
    try:
        r = await provider.route((from_lat, from_lng), dest, mode)
    except ProviderDisabled:
        raise HTTPException(503, "Routing is not configured on the server")
    except ProviderError as exc:
        raise HTTPException(502, str(exc))
    return RouteOut(provider=r.provider, mode=r.mode, distance_m=r.distance_m, duration_s=r.duration_s, geometry=r.geometry)
