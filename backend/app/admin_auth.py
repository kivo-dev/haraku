"""Login rules for the admin panel. Pure Python (no web framework) so it can be unit tested."""
import base64
import hashlib
import secrets
import time
from collections import defaultdict, deque
from typing import Optional

MIN_PASSWORD_LEN = 10
MIN_SECRET_LEN = 32


HASH_SCHEME = "pbkdf2_sha256"
HASH_ITERATIONS = 600_000


def hash_password(password: str, iterations: int = HASH_ITERATIONS, salt: Optional[bytes] = None) -> str:
    """`pbkdf2_sha256$iterations$salt$hash` (base64). Standard library only."""
    salt = salt if salt is not None else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    b64 = lambda b: base64.b64encode(b).decode("ascii")  # noqa: E731
    return f"{HASH_SCHEME}${iterations}${b64(salt)}${b64(digest)}"


def _parse_hash(stored: str) -> Optional[tuple[int, bytes, bytes]]:
    try:
        scheme, iters, salt, digest = stored.split("$")
        if scheme != HASH_SCHEME:
            return None
        n = int(iters)
        if n < 1:
            return None
        return n, base64.b64decode(salt, validate=True), base64.b64decode(digest, validate=True)
    except (ValueError, TypeError):
        return None


def verify_password(password: str, stored: str) -> bool:
    parsed = _parse_hash(stored)
    if parsed is None:
        return False
    iterations, salt, expected = parsed
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return secrets.compare_digest(actual, expected)


def validate_admin_config(username: str, password: str, secret_key: str, password_hash: str = "") -> Optional[str]:
    """None when the admin panel may be switched on, otherwise the reason it stays off."""
    if not username and not password and not secret_key and not password_hash:
        return "ADMIN_USERNAME / ADMIN_PASSWORD(_HASH) / ADMIN_SECRET_KEY are not set"
    if not username:
        return "ADMIN_USERNAME is empty"
    if password_hash:
        if _parse_hash(password_hash) is None:
            return "ADMIN_PASSWORD_HASH is malformed (create it with: python -m app.admin_auth)"
    elif len(password) < MIN_PASSWORD_LEN:
        return f"ADMIN_PASSWORD must be at least {MIN_PASSWORD_LEN} characters"
    if len(secret_key) < MIN_SECRET_LEN:
        return f"ADMIN_SECRET_KEY must be at least {MIN_SECRET_LEN} characters"
    return None


def credentials_ok(username: str, password: str, expected_username: str, expected_password: str) -> bool:
    """Constant-time comparison; both fields are always compared (no early exit on a wrong username)."""
    user_ok = secrets.compare_digest(username.encode("utf-8"), expected_username.encode("utf-8"))
    pass_ok = secrets.compare_digest(password.encode("utf-8"), expected_password.encode("utf-8"))
    return user_ok and pass_ok


def check_login(username: str, password: str, expected_username: str, expected_password: str, expected_hash: str = "") -> bool:
    """Hash wins when configured. Username and password are always both checked (no early exit)."""
    user_ok = secrets.compare_digest(username.encode("utf-8"), expected_username.encode("utf-8"))
    if expected_hash:
        pass_ok = verify_password(password, expected_hash)
    else:
        pass_ok = secrets.compare_digest(password.encode("utf-8"), expected_password.encode("utf-8"))
    return user_ok and pass_ok


class StoreLoginLimiter:
    """Same behaviour as LoginLimiter, but the counters live in a RateStore, so with Redis the block
    holds across workers and restarts."""

    def __init__(self, store, max_failures: int = 5, window_s: int = 600):
        self._store, self.max_failures, self.window_s = store, max_failures, window_s

    def _key(self, ip: str) -> str:
        return f"admin-login:{ip}"

    def blocked(self, ip: str) -> bool:
        return self._store.count(self._key(ip), self.window_s) >= self.max_failures

    def record_failure(self, ip: str) -> None:
        self._store.hit(self._key(ip), self.window_s)

    def reset(self, ip: str) -> None:
        self._store.clear(self._key(ip))


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


if __name__ == "__main__":  # python -m app.admin_auth  ->  prints a hash for ADMIN_PASSWORD_HASH
    import getpass

    pw = getpass.getpass("New admin password: ")
    if len(pw) < MIN_PASSWORD_LEN:
        raise SystemExit(f"Use at least {MIN_PASSWORD_LEN} characters")
    if pw != getpass.getpass("Repeat: "):
        raise SystemExit("Passwords differ")
    print(hash_password(pw))
