from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..mappers import place_to_out
from ..models import Category, Place
from ..schemas import CategoryOut, Localized, PlaceList, PlaceOut
from ..scoring import Candidate, suggest
from ..services.discovery import search_places, visible_places_stmt

router = APIRouter()


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    rows = db.scalars(select(Category).order_by(Category.sort, Category.key)).all()
    return [CategoryOut(key=c.key, title=Localized(fa=c.title_fa, en=c.title_en)) for c in rows]


@router.get("/places", response_model=PlaceList)
def list_places(
    category: Optional[str] = None,
    q: Optional[str] = Query(None, max_length=100, description="Search text (Persian or English)"),
    lat: Optional[float] = Query(None, ge=-90, le=90),
    lng: Optional[float] = Query(None, ge=-180, le=180),
    radius_km: Optional[float] = Query(None, gt=0, le=500, description="Needs lat and lng"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Published places. With `lat`+`lng` the result is sorted by distance and `distanceKm` is filled in."""
    if (lat is None) != (lng is None):
        raise HTTPException(422, "lat and lng must be given together")
    if radius_km is not None and lat is None:
        raise HTTPException(422, "radius_km needs lat and lng")

    page, total = search_places(db, category=category, q=q, lat=lat, lng=lng, radius_km=radius_km, limit=limit, offset=offset)
    return PlaceList(items=[place_to_out(p, d) for p, d in page], total=total, limit=limit, offset=offset)


@router.get("/places/nearby", response_model=PlaceList)
def nearby_places(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(25, gt=0, le=200, description="Search radius around the point"),
    category: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """HARAKO places around a point (the user's GPS position, sent by the frontend), nearest first.
    Only places that have coordinates. The server does not store the position."""
    page, total = search_places(db, category=category, lat=lat, lng=lng, radius_km=radius_km, limit=limit, offset=offset)
    return PlaceList(items=[place_to_out(p, d) for p, d in page], total=total, limit=limit, offset=offset)


@router.get("/places/{place_id}", response_model=PlaceOut)
def get_place(place_id: str, db: Session = Depends(get_db)):
    place = db.scalar(visible_places_stmt().options(selectinload(Place.images)).where(Place.id == place_id))
    if place is None:
        raise HTTPException(404, "Place not found")
    return place_to_out(place, detail=True)


@router.get("/suggestions", response_model=PlaceList)
def get_suggestions(
    response: Response,
    limit: int = Query(6, ge=1, le=20),
    lat: Optional[float] = Query(None, ge=-90, le=90),
    lng: Optional[float] = Query(None, ge=-180, le=180),
    exclude: Optional[str] = Query(None, max_length=1000, description="Comma separated ids shown recently"),
    seed: Optional[int] = Query(None, description="Same seed = same result; leave empty for a fresh pick every time"),
    db: Session = Depends(get_db),
):
    """Places for the "Our suggestions" area. Scoring rules: see app/scoring.py."""
    if (lat is None) != (lng is None):
        raise HTTPException(422, "lat and lng must be given together")
    response.headers["Cache-Control"] = "no-store"  # a refresh must be able to give something new

    rows = db.scalars(visible_places_stmt()).all()
    by_id = {p.id: p for p in rows}
    candidates = [
        Candidate(
            id=p.id,
            category=p.category_key,
            featured=bool(p.featured),
            verified=p.verification == "verified",
            has_image=bool(p.image_url),
            lat=p.lat,
            lng=p.lng,
        )
        for p in rows
    ]
    ids = [i.strip() for i in (exclude or "").split(",") if i.strip()]
    user = (lat, lng) if lat is not None and lng is not None else None
    picked = suggest(candidates, limit=limit, user=user, exclude=ids, seed=seed)
    items = [place_to_out(by_id[s.candidate.id], s.distance_km, s.reason) for s in picked]
    return PlaceList(items=items, total=len(items), limit=limit, offset=0)
