"""Neshan routing adapter. STATUS: UNVERIFIED (see below). Other Neshan capabilities: app/providers/pending.py.

Design rules:
  * the SERVICE key stays on the server (env NESHAN_SERVICE_KEY), never in the frontend;
  * nothing from Neshan is stored in HARAKO's database (licence/terms not checked yet);
  * the rest of the app talks to `RoutingProvider`, so the provider can be swapped later.

!! UNVERIFIED AGAINST THE OFFICIAL DOCS !!
The endpoint, parameters and response shape below are written from memory because the docs were
not reachable when this was written. Before relying on it run:
    python -m app.services.neshan_check 39.29,44.51 39.39,44.38
and compare the printed raw JSON with the docs ("Direction API"). Fix `_parse` if they differ.
"""
import httpx

from ..providers.base import ProviderDisabled, ProviderError, RouteResult, RoutingProvider  # noqa: F401  (re-exported)

BASE_URL = "https://api.neshan.org"
DIRECTION_PATH = "/v4/direction"  # with traffic. Without traffic: /v4/direction/no-traffic


def _parse(data: dict, mode: str) -> RouteResult:
    try:
        route = data["routes"][0]
        leg = route["legs"][0]
        distance = int(round(leg["distance"]["value"]))
        duration = int(round(leg["duration"]["value"]))
        overview = route.get("overview_polyline")
        geometry = overview.get("points") if isinstance(overview, dict) else None
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ProviderError("Unexpected routing response shape") from exc
    return RouteResult("neshan", mode, distance, duration, geometry)


class NeshanRouting:
    def __init__(self, api_key: str, timeout_s: float = 8.0):
        self._key = api_key
        self._timeout = timeout_s

    async def route(self, origin: tuple[float, float], destination: tuple[float, float], mode: str = "car") -> RouteResult:
        if not self._key:
            raise ProviderDisabled("NESHAN_SERVICE_KEY is not set")
        if mode != "car":
            # Pedestrian routing exists at Neshan but its endpoint is not wired until checked in the docs.
            raise ProviderError(f"Mode '{mode}' is not supported yet")
        params = {
            "type": "car",
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                res = await client.get(BASE_URL + DIRECTION_PATH, params=params, headers={"Api-Key": self._key})
        except httpx.HTTPError as exc:
            raise ProviderError("Routing provider unreachable") from exc
        if res.status_code != 200:
            raise ProviderError(f"Routing provider answered with status {res.status_code}")
        try:
            data = res.json()
        except ValueError as exc:
            raise ProviderError("Routing provider returned invalid JSON") from exc
        return _parse(data, mode)
