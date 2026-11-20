"""Login rules for the admin panel. Pure Python (no web framework) so it can be unit tested."""
import secrets
import time
from collections import defaultdict, deque
from typing import Optional

MIN_PASSWORD_LEN = 10
MIN_SECRET_LEN = 32


def validate_admin_config(username: str, password: str, secret_key: str) -> Optional[str]:
    """None when the admin panel may be switched on, otherwise the reason it stays off."""
    if not username and not password and not secret_key:
        return "ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_SECRET_KEY are not set"
    if not username:
        return "ADMIN_USERNAME is empty"
    if len(password) < MIN_PASSWORD_LEN:
        return f"ADMIN_PASSWORD must be at least {MIN_PASSWORD_LEN} characters"
    if len(secret_key) < MIN_SECRET_LEN:
        return f"ADMIN_SECRET_KEY must be at least {MIN_SECRET_LEN} characters"
    return None


def credentials_ok(username: str, password: str, expected_username: str, expected_password: str) -> bool:
    """Constant-time comparison; both fields are always compared (no early exit on a wrong username)."""
    user_ok = secrets.compare_digest(username.encode("utf-8"), expected_username.encode("utf-8"))
    pass_ok = secrets.compare_digest(password.encode("utf-8"), expected_password.encode("utf-8"))
    return user_ok and pass_ok


class LoginLimiter:
    """Blocks an IP after `max_failures` wrong logins within `window_s` seconds (in memory, per process)."""

    def __init__(self, max_failures: int = 5, window_s: float = 600.0):
        self.max_failures = max_failures
        self.window_s = window_s
        self._fails: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, ip: str, now: float) -> deque[float]:
        q = self._fails[ip]
        while q and now - q[0] > self.window_s:
            q.popleft()
        return q

    def blocked(self, ip: str, now: Optional[float] = None) -> bool:
        now = time.monotonic() if now is None else now
        return len(self._prune(ip, now)) >= self.max_failures

    def record_failure(self, ip: str, now: Optional[float] = None) -> None:
        now = time.monotonic() if now is None else now
        self._prune(ip, now).append(now)

    def reset(self, ip: str) -> None:
        self._fails.pop(ip, None)
