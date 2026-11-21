"""Provider contracts. Business logic and routers talk ONLY to these Protocols and dataclasses,
so Neshan (or anything else) can be replaced without touching them.
"""
from dataclasses import dataclass, field
from typing import Optional, Protocol

LatLng = tuple[float, float]


class ProviderError(Exception):
    """The provider failed or answered in a way we do not understand (shown as HTTP 502)."""


class ProviderDisabled(Exception):
    """No key configured (shown as HTTP 503)."""


class ProviderNotImplemented(Exception):
    """The capability is planned but NOT wired yet, because it has not been verified against the
    provider's official documentation or real responses (shown as HTTP 501)."""

    def __init__(self, provider: str, capability: str, message: str = "") -> None:
        self.provider, self.capability = provider, capability
        self.message = message or f"{provider} {capability} is not implemented yet (pending verification against official docs)"
        super().__init__(self.message)


@dataclass
class RouteResult:
    provider: str
    mode: str
    distance_m: int
    duration_s: int
    geometry: Optional[str]  # provider-native encoded polyline; encoding NOT verified yet


@dataclass
class GeocodeResult:
    label: str
    lat: float
    lng: float
    provider: str


@dataclass
class ReverseGeocodeResult:
    label: str
    lat: float
    lng: float
    provider: str
    components: dict[str, str] = field(default_factory=dict)


@dataclass
class PlaceSearchHit:
    title: str
    address: str
    lat: float
    lng: float
    category: Optional[str]
    provider: str


class RoutingProvider(Protocol):
    async def route(self, origin: LatLng, destination: LatLng, mode: str = "car") -> RouteResult: ...


class GeocodingProvider(Protocol):
    async def geocode(self, query: str, near: Optional[LatLng] = None) -> list[GeocodeResult]: ...

    async def reverse(self, lat: float, lng: float) -> Optional[ReverseGeocodeResult]: ...


class PlaceSearchProvider(Protocol):
    async def search(self, query: str, near: Optional[LatLng] = None) -> list[PlaceSearchHit]: ...
