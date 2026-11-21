from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # dev | test | prod. "dev" creates tables automatically; "prod" requires Alembic migrations
    # and refuses to start when app/prodcheck.py finds an unsafe configuration.
    app_env: str = "dev"
    # SQLite is fine on a laptop. With Docker Compose / production use PostgreSQL:
    #   postgresql+psycopg://harako:password@db:5432/harako
    database_url: str = "sqlite:///./harako.db"
    # Comma separated browser origins allowed to call the API (the frontend address).
    cors_origins: str = "http://localhost:3000"
    # Placeholder records (source "seed-sample") are visible in dev; set false in production.
    expose_sample_data: bool = True

    # --- Neshan (server side only; NEVER in the frontend or Git). Empty = provider switched off.
    neshan_service_key: str = ""
    neshan_timeout_s: float = 8.0

    # --- Rate limiting. Paid provider endpoints cost quota, so they are limited.
    route_requests_per_minute: int = 20  # per client IP, /v1/route
    geo_requests_per_minute: int = 30  # per client IP, /v1/geo/*
    tools_paid_requests_per_minute: int = 60  # all AI-tool calls that hit a paid provider, in total
    # Shared counters for several workers/servers. Empty = in-memory (single process only).
    redis_url: str = ""
    # Number of reverse proxies in front of the API that append to X-Forwarded-For (0 = do not trust it).
    trusted_proxy_count: int = 0
    # Mirror of uvicorn's WEB_CONCURRENCY. Prod refuses >1 worker without REDIS_URL.
    web_concurrency: int = 1

    # --- Admin panel (/admin). Stays OFF unless username + password(-hash) + secret are valid.
    admin_username: str = ""
    admin_password: str = ""  # plaintext (dev only; prod requires the hash below)
    admin_password_hash: str = ""  # output of: python -m app.admin_auth
    admin_secret_key: str = ""  # >= 32 random chars, signs the session cookie
    admin_cookie_secure: Optional[bool] = None  # None = true in prod, false otherwise
    admin_session_max_age_s: int = 8 * 3600
    admin_login_max_failures: int = 5
    admin_login_window_s: int = 600
    # Extra hosts (host[:port], comma separated) that may POST to /admin, e.g. behind a rewriting proxy.
    admin_allowed_origins: str = ""

    # --- AI assistant tool endpoints (/v1/tools/*), called server-to-server by the AI service.
    tools_enabled: bool = True
    tools_api_key: str = ""  # sent as header X-Tools-Key. Required in prod when tools are enabled.

    @property
    def is_prod(self) -> bool:
        return self.app_env == "prod"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def admin_allowed_origin_list(self) -> list[str]:
        return [o.strip().lower() for o in self.admin_allowed_origins.split(",") if o.strip()]

    @property
    def admin_cookie_https_only(self) -> bool:
        return self.is_prod if self.admin_cookie_secure is None else self.admin_cookie_secure


@lru_cache
def get_settings() -> Settings:
    return Settings()
