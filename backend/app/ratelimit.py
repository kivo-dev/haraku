"""FastAPI rate-limit dependencies on top of app/ratestore.py.

    check_route_limit   /v1/route          per client IP
    check_geo_limit     /v1/geo/*          per client IP
    check_tools_paid_limit  AI tool calls that reach a paid provider, counted in total (the AI service
                            is one caller, so a per-IP limit would throttle the whole assistant)
"""
import logging
from functools import lru_cache

from fastapi import HTTPException, Request

from .config import get_settings
from .ratestore import FallbackStore, MemoryStore, RateStore, RedisStore, pick_client_ip

log = logging.getLogger("harako.ratelimit")


@lru_cache
def get_store() -> RateStore:
    url = get_settings().redis_url
    if not url:
        return MemoryStore()
    try:
        import redis  # imported lazily: only needed when REDIS_URL is set

        client = redis.Redis.from_url(url, socket_timeout=1, socket_connect_timeout=1)
        return FallbackStore(RedisStore(client))
    except Exception:  # noqa: BLE001
        log.warning("Could not set up Redis for rate limiting, using per-process memory")
        return MemoryStore()


def client_ip(request: Request) -> str:
    return pick_client_ip(
        request.headers.get("x-forwarded-for"),
        request.client.host if request.client else None,
        get_settings().trusted_proxy_count,
    )


def _limiter(name: str, setting: str, per_ip: bool):
    def dependency(request: Request) -> None:
        limit = getattr(get_settings(), setting)
        key = f"{name}:{client_ip(request)}" if per_ip else name
        if get_store().hit(key, 60) > limit:
            raise HTTPException(429, "Too many requests, try again in a minute", headers={"Retry-After": "60"})

    return dependency


check_route_limit = _limiter("route", "route_requests_per_minute", per_ip=True)
check_geo_limit = _limiter("geo", "geo_requests_per_minute", per_ip=True)
check_tools_paid_limit = _limiter("tools-paid", "tools_paid_requests_per_minute", per_ip=False)
