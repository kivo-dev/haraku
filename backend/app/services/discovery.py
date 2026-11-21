"""HARAKO's own place discovery (database only; no external provider is involved here).

Shared by /v1/places, /v1/places/nearby and the AI tool endpoints so they can never disagree.
"""
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..constants import PUBLISHED, SAMPLE_SOURCE
from ..geo import bounding_box, haversine_km
from ..models import Opportunity, Place
from ..search_text import query_keys


def visible_places_stmt():
    """Published places. Placeholder records are excluded when EXPOSE_SAMPLE_DATA=false."""
    stmt = select(Place).where(Place.status == PUBLISHED)
    if not get_settings().expose_sample_data:
        stmt = stmt.where(Place.source != SAMPLE_SOURCE)
    return stmt


def visible_opportunities_stmt():
    stmt = select(Opportunity).where(Opportunity.status == PUBLISHED)
    if not get_settings().expose_sample_data:
        stmt = stmt.where(Opportunity.source != SAMPLE_SOURCE)
    return stmt


def search_places(
    db: Session,
    *,
    category: Optional[str] = None,
    q: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[tuple[Place, Optional[float]]], int]:
    """Returns ([(place, distance_km or None)], total). Callers validate lat/lng pairing first.
    With coordinates: only places that HAVE coordinates, sorted by distance (then id)."""
    stmt = visible_places_stmt()
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
        return with_dist[offset : offset + limit], len(with_dist)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Place.featured.desc(), Place.name_fa, Place.id).limit(limit).offset(offset)).all()
    return [(p, None) for p in rows], total
