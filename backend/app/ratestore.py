"""Counters behind the rate limiters. Pure Python (no web framework) so they are easy to test.

MemoryStore  sliding window, per process        -> fine for one worker / development
RedisStore   fixed window shared by all workers -> needed for several workers or servers
FallbackStore uses Redis, and if Redis fails switches to memory for that call (and logs it), so a
              Redis outage degrades the limiter instead of taking the API down.
"""
import logging
import threading
import time
from collections import defaultdict, deque
from typing import Any, Optional, Protocol

log = logging.getLogger("harako.ratelimit")


class RateStore(Protocol):
    def hit(self, key: str, window_s: int) -> int: ...  # record one event, return events in the window
    def count(self, key: str, window_s: int) -> int: ...  # events in the window, without recording
    def clear(self, key: str) -> None: ...


class MemoryStore:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, window_s: int, now: float) -> deque[float]:
        q = self._events[key]
        while q and now - q[0] > window_s:
            q.popleft()
        return q

    def hit(self, key: str, window_s: int, now: Optional[float] = None) -> int:
        now = time.monotonic() if now is None else now
        with self._lock:
            q = self._prune(key, window_s, now)
            q.append(now)
            return len(q)

    def count(self, key: str, window_s: int, now: Optional[float] = None) -> int:
        now = time.monotonic() if now is None else now
        with self._lock:
            return len(self._prune(key, window_s, now))

    def clear(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)


class RedisStore:
    """`client` is a redis.Redis (anything with incr/expire/get/delete). Fixed window: the first hit
    starts the window, which then expires by itself."""

    def __init__(self, client: Any, prefix: str = "harako:rl:") -> None:
        self._r = client
        self._prefix = prefix

    def hit(self, key: str, window_s: int) -> int:
        k = self._prefix + key
        n = int(self._r.incr(k))
        if n == 1:
            self._r.expire(k, window_s)
        return n

    def count(self, key: str, window_s: int) -> int:  # noqa: ARG002
        return int(self._r.get(self._prefix + key) or 0)

    def clear(self, key: str) -> None:
        self._r.delete(self._prefix + key)


class FallbackStore:
    def __init__(self, primary: RateStore, fallback: Optional[RateStore] = None) -> None:
        self._primary = primary
        self._fallback = fallback or MemoryStore()
        self._warned = False

    def _call(self, name: str, *args: Any) -> Any:
        try:
            return getattr(self._primary, name)(*args)
        except Exception:  # noqa: BLE001 - any Redis problem must not break the request
            if not self._warned:
                log.warning("Rate-limit store unavailable, using per-process memory instead")
                self._warned = True
            return getattr(self._fallback, name)(*args)

    def hit(self, key: str, window_s: int) -> int:
        return self._call("hit", key, window_s)

    def count(self, key: str, window_s: int) -> int:
        return self._call("count", key, window_s)

    def clear(self, key: str) -> None:
        self._call("clear", key)


def pick_client_ip(forwarded_for: Optional[str], peer: Optional[str], trusted_proxies: int) -> str:
    """With N trusted proxies in front, the client is the N-th entry from the RIGHT of X-Forwarded-For
    (each trusted proxy appends the address it saw). With 0 the header is ignored, because anybody
    can send it."""
    if trusted_proxies > 0 and forwarded_for:
        parts = [p.strip() for p in forwarded_for.split(",") if p.strip()]
        if len(parts) >= trusted_proxies:
            return parts[-trusted_proxies]
    return peer or "unknown"
