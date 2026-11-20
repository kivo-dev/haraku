"""Suggestion engine (v1): a simple, explainable scoring system. No AI.

Score of a place =
    + FEATURED_BONUS      if the team marked it as featured
    + VERIFIED_BONUS      if its information was checked
    + IMAGE_BONUS         if it has a photo
    + proximity bonus     if the user's position is known (closer = more)
    + random jitter       so every refresh can look different (pass `seed` for a repeatable result)
and while picking one by one:
    - REPEAT_CATEGORY_PENALTY for each already-picked place of the same category (variety)
    - RECENT_PENALTY          if the client says it was shown recently (`exclude`)

Only facts that are really true are returned as the `reason`.
"""
import random
from dataclasses import dataclass
from typing import Iterable, Optional

from .geo import haversine_km

FEATURED_BONUS = 3.0
VERIFIED_BONUS = 1.0
IMAGE_BONUS = 0.5
PROXIMITY_MAX = 2.5
PROXIMITY_HALF_KM = 15.0  # at this distance the proximity bonus is half of the maximum
NEAR_KM = 25.0  # "near you" is only claimed inside this distance
JITTER = 1.5
# Variety first: a repeat costs as much as the biggest "luck" a place can have (featured + jitter), so while
# a category that has not been shown yet exists, a repeat of an equally good category loses to it.
REPEAT_CATEGORY_PENALTY = FEATURED_BONUS + JITTER
RECENT_PENALTY = 3.0


@dataclass(frozen=True)
class Candidate:
    id: str
    category: str
    featured: bool = False
    verified: bool = False
    has_image: bool = False
    lat: Optional[float] = None
    lng: Optional[float] = None


@dataclass(frozen=True)
class Suggestion:
    candidate: Candidate
    score: float
    reason: Optional[str]  # "near" | "featured" | None
    distance_km: Optional[float]


def suggest(
    candidates: Iterable[Candidate],
    limit: int = 6,
    user: Optional[tuple[float, float]] = None,
    exclude: Iterable[str] = (),
    seed: Optional[int] = None,
) -> list[Suggestion]:
    rng = random.Random(seed)
    recent = set(exclude)

    scored: list[tuple[Candidate, float, Optional[float]]] = []
    for c in candidates:
        base = 0.0
        if c.featured:
            base += FEATURED_BONUS
        if c.verified:
            base += VERIFIED_BONUS
        if c.has_image:
            base += IMAGE_BONUS
        dist: Optional[float] = None
        if user is not None and c.lat is not None and c.lng is not None:
            dist = haversine_km(user[0], user[1], c.lat, c.lng)
            base += PROXIMITY_MAX * PROXIMITY_HALF_KM / (PROXIMITY_HALF_KM + dist)
        base += rng.uniform(0, JITTER)
        scored.append((c, base, dist))

    picked: list[Suggestion] = []
    per_category: dict[str, int] = {}
    pool = scored[:]
    while pool and len(picked) < limit:
        def adjusted(item: tuple[Candidate, float, Optional[float]]) -> float:
            c, base, _ = item
            s = base - REPEAT_CATEGORY_PENALTY * per_category.get(c.category, 0)
            if c.id in recent:
                s -= RECENT_PENALTY
            return s

        best = max(pool, key=lambda it: (adjusted(it), it[0].id))  # id breaks ties deterministically
        pool.remove(best)
        c, _, dist = best
        per_category[c.category] = per_category.get(c.category, 0) + 1
        if dist is not None and dist <= NEAR_KM:
            reason: Optional[str] = "near"
        elif c.featured:
            reason = "featured"
        else:
            reason = None
        picked.append(Suggestion(c, adjusted(best), reason, dist))
    return picked
