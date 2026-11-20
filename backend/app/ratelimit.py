"""Tiny in-memory rate limiter (per client IP, per process). Enough to stop accidents and simple abuse
of the routing endpoint, which costs provider quota. For several server processes use Redis later."""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from .config import get_settings

_hits: dict[str, deque[float]] = defaultdict(deque)


def check_route_limit(request: Request) -> None:
    limit = get_settings().route_requests_per_minute
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(429, "Too many route requests, try again in a minute")
    q.append(now)
