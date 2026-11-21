"""Geocoding / reverse geocoding / external search.

CONTRACT IS FINAL, IMPLEMENTATION IS PENDING: until the Neshan adapters are verified against the
official documentation, these answer HTTP 501 with
  {"detail": {"code": "provider_not_implemented", "provider": "neshan", "capability": "...", "message": "..."}}
Results, once available, are always `data_source: "external"` and `verified: false`.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..providers.base import GeocodingProvider, PlaceSearchProvider
from ..providers.registry import get_geocoding_provider, get_place_search_provider
from ..ratelimit import check_geo_limit
from ..schemas_tools import ExternalPlace, GeocodeOut, ReverseGeocodeOut

router = APIRouter(dependencies=[Depends(check_geo_limit)])


def _near(lat: Optional[float], lng: Optional[float]):
    if (lat is None) != (lng is None):
        raise HTTPException(422, "lat and lng must be given together")
    return (lat, lng) if lat is not None and lng is not None else None


@router.get("/geo/geocode", response_model=GeocodeOut)
async def geocode(
    q: str = Query(..., min_length=2, max_length=200, description="Address or place text"),
    lat: Optional[float] = Query(None, ge=-90, le=90, description="Optional bias point"),
    lng: Optional[float] = Query(None, ge=-180, le=180),
    provider: GeocodingProvider = Depends(get_geocoding_provider),
):
    res = await provider.geocode(q, _near(lat, lng))
    return GeocodeOut(
        query=q,
        provider=res[0].provider if res else "none",
        results=[ExternalPlace(label=r.label, lat=r.lat, lng=r.lng, provider=r.provider) for r in res],
    )


@router.get("/geo/reverse", response_model=ReverseGeocodeOut)
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    provider: GeocodingProvider = Depends(get_geocoding_provider),
):
    r = await provider.reverse(lat, lng)
    if r is None:
        return ReverseGeocodeOut(lat=lat, lng=lng, provider="none")
    return ReverseGeocodeOut(lat=lat, lng=lng, provider=r.provider, label=r.label, components=r.components)


@router.get("/geo/search", response_model=GeocodeOut)
async def search_external(
    q: str = Query(..., min_length=2, max_length=200),
    lat: Optional[float] = Query(None, ge=-90, le=90),
    lng: Optional[float] = Query(None, ge=-180, le=180),
    provider: PlaceSearchProvider = Depends(get_place_search_provider),
):
    """External (provider) place search. Separate from /v1/places on purpose: these are NOT verified
    HARAKO places."""
    hits = await provider.search(q, _near(lat, lng))
    return GeocodeOut(
        query=q,
        provider=hits[0].provider if hits else "none",
        results=[ExternalPlace(label=h.title, address=h.address, category=h.category, lat=h.lat, lng=h.lng, provider=h.provider) for h in hits],
    )
