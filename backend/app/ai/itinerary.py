"""Pure itinerary helpers (no I/O). Ordering uses straight-line distance only to CHOOSE an order;
real times always come from the routing provider."""
import itertools
from dataclasses import dataclass
from typing import Any, Optional

from ..geo import haversine_km

MAX_STOPS = 6  # 6! = 720 orders: exact search is instant


@dataclass(frozen=True)
class Stop:
    id: str
    name: str
    lat: float
    lng: float


def best_order(start: Optional[tuple[float, float]], stops: list[Stop]) -> list[Stop]:
    """Shortest open path (by straight-line km) through all stops. Without `start` any stop may be first."""
    if len(stops) > MAX_STOPS:
        raise ValueError("too many stops")
    best: Optional[tuple[float, tuple[str, ...], list[Stop]]] = None
    for perm in itertools.permutations(stops):
        total, prev = 0.0, start
        for s in perm:
            if prev is not None:
                total += haversine_km(prev[0], prev[1], s.lat, s.lng)
            prev = (s.lat, s.lng)
        key = (round(total, 6), tuple(s.id for s in perm))
        if best is None or key < (best[0], best[1]):
            best = (key[0], key[1], list(perm))
    return best[2] if best else []


def summarize(legs: list[dict[str, Any]], available_hours: Optional[float]) -> dict[str, Any]:
    """Totals only when EVERY leg has a provider-measured time. Never claims the plan is feasible:
    visit durations are not in HARAKO's data, so only the travel part can be checked."""
    all_routed = bool(legs) and all(l["source"] == "routing" for l in legs)
    total_min = round(sum(l["duration_min"] for l in legs)) if all_routed else None
    total_km = round(sum(l["distance_km"] for l in legs), 1) if all_routed else None
    fits: Optional[bool] = None
    if total_min is not None and available_hours is not None:
        fits = total_min <= available_hours * 60
    return {
        "total_travel_min": total_min,
        "total_distance_km": total_km,
        "travel_time_fits_available_time": fits,
        "visit_durations_known": False,
    }
