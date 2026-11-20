"""Data access for the assistant tools.

`TourismData` is the ONLY door from the AI to HARAKO's data and to the routing provider.
`DbTourismData` implements it by calling the EXISTING route functions (same queries, same filters,
same 'published only' rule as the public API) and the EXISTING NeshanRouting adapter: nothing is duplicated.
The model never sees SQL, sessions or keys."""
import asyncio
from typing import Any, Optional, Protocol

from .errors import ToolError


class TourismData(Protocol):
    async def search_places(
        self, *, query: Optional[str], category: Optional[str], limit: int,
        lat: Optional[float] = None, lng: Optional[float] = None, radius_km: Optional[float] = None,
    ) -> tuple[list[dict[str, Any]], int]: ...

    async def get_place(self, place_id: str) -> Optional[dict[str, Any]]: ...

    async def list_categories(self) -> list[dict[str, Any]]: ...

    async def search_opportunities(self, *, query: Optional[str], sector: Optional[str], limit: int) -> list[dict[str, Any]]: ...

    async def route(self, origin: tuple[float, float], destination: tuple[float, float], mode: str) -> dict[str, Any]:
        """-> {provider, mode, distance_m, duration_s, geometry}. Raises ToolError on any failure."""
        ...


class DbTourismData:
    def __init__(self, db, settings):
        self.db, self.settings = db, settings

    async def search_places(self, *, query, category, limit, lat=None, lng=None, radius_km=None):
        def run():
            from fastapi import HTTPException

            from ..routers.places import list_places

            try:
                res = list_places(category=category, q=query, lat=lat, lng=lng, radius_km=radius_km, limit=limit, offset=0, db=self.db)
            except HTTPException as exc:
                raise ToolError("invalid_arguments", str(exc.detail)) from exc
            return [p.model_dump() for p in res.items], res.total

        return await asyncio.to_thread(run)

    async def get_place(self, place_id):
        def run():
            from fastapi import HTTPException

            from ..routers.places import get_place

            try:
                return get_place(place_id=place_id, db=self.db).model_dump()
            except HTTPException:
                return None

        return await asyncio.to_thread(run)

    async def list_categories(self):
        def run():
            from ..routers.places import list_categories

            return [c.model_dump() for c in list_categories(db=self.db)]

        return await asyncio.to_thread(run)

    async def search_opportunities(self, *, query, sector, limit):
        def run():
            from ..routers.opportunities import list_opportunities

            return [o.model_dump() for o in list_opportunities(sector=sector, q=query, db=self.db).items][:limit]

        return await asyncio.to_thread(run)

    async def route(self, origin, destination, mode):
        from ..services.neshan import NeshanRouting, ProviderDisabled, ProviderError

        if mode != "car":
            raise ToolError("mode_unsupported", f"Only driving routes are available right now (asked: {mode}).")
        provider = NeshanRouting(self.settings.neshan_service_key, self.settings.neshan_timeout_s)
        try:
            r = await provider.route(origin, destination, mode)
        except ProviderDisabled:
            raise ToolError("routing_not_configured", "Routing is not configured on the server.")
        except ProviderError:
            raise ToolError("routing_unavailable", "The routing service failed or is unreachable.")
        return {"provider": r.provider, "mode": r.mode, "distance_m": r.distance_m, "duration_s": r.duration_s, "geometry": r.geometry}
