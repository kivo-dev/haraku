"""Single place that decides which provider implements which capability.
FastAPI dependencies below are overridden in tests with fakes."""
from .base import GeocodingProvider, PlaceSearchProvider, RoutingProvider
from .pending import PendingNeshanGeocoding, PendingNeshanPlaceSearch
from ..config import get_settings


def get_routing_provider() -> RoutingProvider:
    from ..services.neshan import NeshanRouting  # unverified adapter, see its docstring

    s = get_settings()
    return NeshanRouting(s.neshan_service_key, s.neshan_timeout_s)


def get_geocoding_provider() -> GeocodingProvider:
    return PendingNeshanGeocoding()


def get_place_search_provider() -> PlaceSearchProvider:
    return PendingNeshanPlaceSearch()


# State vocabulary:  verified   checked against official docs / real response, covered by tests
#                    unverified implemented from memory; must be checked before production use
#                    pending    not implemented, endpoints answer HTTP 501
#                    off        implemented but switched off (no key)
def capability_status() -> list[dict]:
    key = bool(get_settings().neshan_service_key)
    return [
        {"capability": "routing_car", "provider": "neshan", "state": "unverified" if key else "off",
         "key_configured": key, "note": "Endpoint/response parsing written from memory. Run `python -m app.services.neshan_check` and compare with the official docs."},
        {"capability": "routing_pedestrian", "provider": "neshan", "state": "pending", "key_configured": key, "note": "Not wired."},
        {"capability": "route_alternatives", "provider": "neshan", "state": "pending", "key_configured": key, "note": "Not wired."},
        {"capability": "geocode", "provider": "neshan", "state": "pending", "key_configured": key, "note": "Not wired."},
        {"capability": "reverse_geocode", "provider": "neshan", "state": "pending", "key_configured": key, "note": "Not wired."},
        {"capability": "place_search", "provider": "neshan", "state": "pending", "key_configured": key, "note": "Not wired."},
        {"capability": "harako_places", "provider": "harako", "state": "verified", "key_configured": True, "note": "Own database."},
    ]
