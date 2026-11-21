"""PENDING Neshan capabilities.

These classes exist so the API contract (routes, schemas, AI tool manifest) is stable NOW. Every
method raises ProviderNotImplemented (HTTP 501). Nothing here calls the network and nothing here
guesses a Neshan URL, header, parameter or response shape.

To implement one: read the official Neshan documentation (or capture a real response), write the
adapter in app/providers/neshan_<capability>.py, add mocked-response tests, then switch the factory
in app/providers/registry.py. Until then the capability must keep reporting state "pending".
"""
from typing import Optional

from .base import (
    GeocodeResult,
    LatLng,
    PlaceSearchHit,
    ProviderNotImplemented,
    ReverseGeocodeResult,
)

PROVIDER = "neshan"


class PendingNeshanGeocoding:
    async def geocode(self, query: str, near: Optional[LatLng] = None) -> list[GeocodeResult]:  # noqa: ARG002
        raise ProviderNotImplemented(PROVIDER, "geocode")

    async def reverse(self, lat: float, lng: float) -> Optional[ReverseGeocodeResult]:  # noqa: ARG002
        raise ProviderNotImplemented(PROVIDER, "reverse_geocode")


class PendingNeshanPlaceSearch:
    async def search(self, query: str, near: Optional[LatLng] = None) -> list[PlaceSearchHit]:  # noqa: ARG002
        raise ProviderNotImplemented(PROVIDER, "place_search")
