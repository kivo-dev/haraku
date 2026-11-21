"""Stable contracts for the geo endpoints and the AI-assistant tools.

These are NEW shapes (the website's /v1/places shapes are untouched). Rules for every consumer:
  * `data_source` says where a record came from. "harako_db" = HARAKO's own database;
    "external" = a map provider result. External results are NEVER `verified`.
  * unknown values are null, never guessed.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from .schemas import CategoryOut, Localized, OpportunityList  # noqa: F401  (re-exported for the tools)


class Coordinates(BaseModel):
    lat: float
    lng: float


class ToolPlace(BaseModel):
    id: str
    category: str
    name: Localized
    area: Localized
    summary: Localized
    coordinates: Optional[Coordinates] = None  # null when the record has no coordinates yet
    distance_km: Optional[float] = None  # only when the caller sent a position
    rating: Optional[float] = None
    verified: bool
    verification_status: str  # verified | unverified
    last_verified_at: Optional[datetime] = None
    data_source: Literal["harako_db"] = "harako_db"
    record_source: str  # how the record entered the database: manual | seed-sample | ...
    is_sample: bool  # True = placeholder content, never present it as a real fact


class ToolPlaceList(BaseModel):
    items: list[ToolPlace]
    total: int
    limit: int
    offset: int
    data_source: Literal["harako_db"] = "harako_db"


class ToolRoute(BaseModel):
    provider: str
    provider_status: str  # verified | unverified  (state of the provider adapter, see /v1/providers/status)
    mode: str
    distance_m: int
    duration_s: int
    geometry: Optional[str] = None
    geometry_encoding: str = "provider_native_unverified"
    destination: Coordinates
    destination_place_id: Optional[str] = None


class ExternalPlace(BaseModel):
    """A result from a map provider. NOT a HARAKO tourism recommendation."""

    label: str
    address: Optional[str] = None
    category: Optional[str] = None
    lat: float
    lng: float
    provider: str
    data_source: Literal["external"] = "external"
    verified: Literal[False] = False


class GeocodeOut(BaseModel):
    query: str
    provider: str
    results: list[ExternalPlace]


class ReverseGeocodeOut(BaseModel):
    lat: float
    lng: float
    provider: str
    label: Optional[str] = None
    components: dict[str, str] = {}
    data_source: Literal["external"] = "external"


class ProviderCapability(BaseModel):
    capability: str
    provider: str
    state: Literal["verified", "unverified", "pending", "off"]
    key_configured: bool
    note: str


class ProviderStatusOut(BaseModel):
    capabilities: list[ProviderCapability]
    note: str = "Reports configuration state only. It does not call any provider."
