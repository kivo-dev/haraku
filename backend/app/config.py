from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # "dev" creates tables automatically; use Alembic migrations in "prod".
    app_env: str = "dev"
    # SQLite is fine on a laptop. With Docker Compose / production use PostgreSQL:
    #   postgresql+psycopg://harako:password@db:5432/harako
    database_url: str = "sqlite:///./harako.db"
    # Comma separated browser origins allowed to call the API (the frontend address).
    cors_origins: str = "http://localhost:3000"

    # Neshan SERVICE key (the one for web services such as routing). Server side only.
    # NEVER use it in the frontend or commit it to Git. Empty = routing is switched off.
    neshan_service_key: str = ""
    neshan_timeout_s: float = 8.0
    # Routing costs quota, so it is limited per client IP (in memory, per process).
    route_requests_per_minute: int = 20

    # Admin panel (/admin). Stays OFF unless all three are set (see .env.example).
    admin_username: str = ""
    admin_password: str = ""  # at least 10 characters
    admin_secret_key: str = ""  # at least 32 random characters, signs the login cookie

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
