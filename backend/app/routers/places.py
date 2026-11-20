from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..geo import bounding_box, haversine_km
from ..mappers import place_to_out
from ..models import PUBLISHED, Category, Place
from ..schemas import CategoryOut, Localized, PlaceList, PlaceOut
from ..scoring import Candidate, suggest
from ..search_text import query_keys

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

    stmt = select(Place).where(Place.status == PUBLISHED)
    if category:
        stmt = stmt.where(Place.category_key == category)
    keys = query_keys(q)
    if keys:
        n, c = keys
        stmt = stmt.where(or_(Place.search_text.contains(n, autoescape=True), Place.search_compact.contains(c, autoescape=True)))

    if lat is not None and lng is not None:
        stmt = stmt.where(Place.lat.is_not(None), Place.lng.is_not(None))
        if radius_km is not None:
            min_lat, max_lat, min_lng, max_lng = bounding_box(lat, lng, radius_km)
            stmt = stmt.where(Place.lat.between(min_lat, max_lat), Place.lng.between(min_lng, max_lng))
        rows = db.scalars(stmt).all()
        with_dist = [(p, haversine_km(lat, lng, p.lat, p.lng)) for p in rows]
        if radius_km is not None:
            with_dist = [(p, d) for p, d in with_dist if d <= radius_km]
        with_dist.sort(key=lambda pd: (pd[1], pd[0].id))
        page = with_dist[offset : offset + limit]
        return PlaceList(items=[place_to_out(p, d) for p, d in page], total=len(with_dist), limit=limit, offset=offset)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Place.featured.desc(), Place.name_fa, Place.id).limit(limit).offset(offset)).all()
    return PlaceList(items=[place_to_out(p) for p in rows], total=total, limit=limit, offset=offset)


@router.get("/places/{place_id}", response_model=PlaceOut)
def get_place(place_id: str, db: Session = Depends(get_db)):
    place = db.scalar(select(Place).options(selectinload(Place.images)).where(Place.id == place_id, Place.status == PUBLISHED))
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

    rows = db.scalars(select(Place).where(Place.status == PUBLISHED)).all()
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
