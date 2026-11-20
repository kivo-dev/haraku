"""Response shapes. They match what the frontend's `normalizePlace` / `normalizeOpportunity` read
(`name`/`area`/`summary` as {fa, en}, `lat`/`lng`, `distanceKm`, `image`, `featured`, `reason`)."""
from typing import Optional

from pydantic import BaseModel


class Localized(BaseModel):
    fa: str
    en: str


class PlaceOut(BaseModel):
    id: str
    category: str
    name: Localized
    area: Localized
    summary: Localized
    lat: Optional[float] = None
    lng: Optional[float] = None
    rating: Optional[float] = None
    distanceKm: Optional[float] = None
    featured: bool = False
    image: Optional[str] = None
    images: list[str] = []  # detail endpoint only
    reason: Optional[Localized] = None  # suggestions endpoint only
    verified: bool = False


class PlaceList(BaseModel):
    items: list[PlaceOut]
    total: int
    limit: int
    offset: int


class CategoryOut(BaseModel):
    key: str
    title: Localized


class OpportunityOut(BaseModel):
    id: str
    sector: str
    title: Localized
    summary: Localized
    image: Optional[str] = None
    verified: bool = False


class OpportunityList(BaseModel):
    items: list[OpportunityOut]
    total: int


class RouteOut(BaseModel):
    provider: str
    mode: str
    distance_m: int
    duration_s: int
    geometry: Optional[str] = None  # encoded polyline exactly as the provider returned it
