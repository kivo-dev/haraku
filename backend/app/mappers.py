"""Database rows -> response objects. Duck-typed on purpose (easy to unit test)."""
from typing import Any, Optional

from .constants import VERIFIED
from .schemas import Localized, OpportunityOut, PlaceOut

REASONS = {
    "near": Localized(fa="نزدیک شما", en="Near you"),
    "featured": Localized(fa="از مکان‌های منتخب", en="Featured"),
}


def _loc(fa: Optional[str], en: Optional[str]) -> Localized:
    fa, en = fa or "", en or ""
    return Localized(fa=fa or en, en=en or fa)  # never leave one language empty


def place_to_out(p: Any, distance_km: Optional[float] = None, reason: Optional[str] = None, detail: bool = False) -> PlaceOut:
    return PlaceOut(
        id=p.id,
        category=p.category_key,
        name=_loc(p.name_fa, p.name_en),
        area=_loc(p.area_fa, p.area_en),
        summary=_loc(p.summary_fa, p.summary_en),
        lat=p.lat,
        lng=p.lng,
        rating=p.rating,
        distanceKm=round(distance_km, 1) if distance_km is not None else None,
        featured=bool(p.featured),
        image=p.image_url or None,
        images=[i.url for i in p.images] if detail else [],
        reason=REASONS.get(reason) if reason else None,
        verified=p.verification == VERIFIED,
        source=getattr(p, "source", "manual"),
        is_sample=getattr(p, "source", "manual") == "seed-sample",
    )


def opportunity_to_out(o: Any) -> OpportunityOut:
    return OpportunityOut(
        id=o.id,
        sector=o.sector,
        title=_loc(o.title_fa, o.title_en),
        summary=_loc(o.summary_fa, o.summary_en),
        image=o.image_url or None,
        verified=o.verification == VERIFIED,
        source=getattr(o, "source", "manual"),
        is_sample=getattr(o, "source", "manual") == "seed-sample",
    )
