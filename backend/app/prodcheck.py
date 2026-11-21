"""Production configuration checks. Duck-typed on the settings object so they are easy to unit test.
In prod the app REFUSES to start while `production_problems` is not empty (fail safe, not fail open)."""
from typing import Any
from urllib.parse import urlsplit

from .admin_auth import validate_admin_config


def _bad_origin(origin: str) -> str | None:
    if origin == "*":
        return "CORS_ORIGINS must not contain '*'"
    parts = urlsplit(origin)
    # Capacitor's Android WebView uses https://localhost (iOS: capacitor://localhost); those are fine.
    if parts.scheme == "http":
        return f"CORS_ORIGINS has a plain-http origin ({origin}); use https"
    if not parts.scheme or not parts.netloc:
        return f"CORS_ORIGINS has an invalid origin ({origin})"
    return None


def production_problems(s: Any) -> list[str]:
    if s.app_env != "prod":
        return []
    out: list[str] = []
    if s.database_url.startswith("sqlite"):
        out.append("DATABASE_URL must be PostgreSQL in production (SQLite is for development)")
    origins = s.cors_origin_list
    if not origins:
        out.append("CORS_ORIGINS is empty")
    for o in origins:
        msg = _bad_origin(o)
        if msg:
            out.append(msg)
    if s.expose_sample_data:
        out.append("EXPOSE_SAMPLE_DATA must be false in production (placeholder records would look real)")
    if s.web_concurrency > 1 and not s.redis_url:
        out.append("WEB_CONCURRENCY > 1 needs REDIS_URL, otherwise rate limits are per worker")
    if s.tools_enabled and not s.tools_api_key:
        out.append("TOOLS_API_KEY is required while TOOLS_ENABLED=true")
    admin_touched = any([s.admin_username, s.admin_password, s.admin_password_hash, s.admin_secret_key])
    if admin_touched:
        why = validate_admin_config(s.admin_username, s.admin_password, s.admin_secret_key, s.admin_password_hash)
        if why:
            out.append(f"Admin configuration invalid: {why}")
        if s.admin_password and not s.admin_password_hash:
            out.append("Use ADMIN_PASSWORD_HASH (python -m app.admin_auth), not a plaintext ADMIN_PASSWORD, in production")
        if s.admin_cookie_secure is False:
            out.append("ADMIN_COOKIE_SECURE must not be false in production")
    return out


def production_warnings(s: Any) -> list[str]:
    out: list[str] = []
    if not s.neshan_service_key:
        out.append("NESHAN_SERVICE_KEY is empty: routing is switched off")
    if s.app_env == "prod" and not s.redis_url:
        out.append("REDIS_URL is empty: rate limits live in each process's memory")
    return out


def assert_production_ready(s: Any) -> None:
    problems = production_problems(s)
    if problems:
        raise RuntimeError("Unsafe production configuration:\n - " + "\n - ".join(problems))
