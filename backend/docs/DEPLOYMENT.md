# Deployment

## Environment variables (names only)
`APP_ENV, DATABASE_URL, CORS_ORIGINS, EXPOSE_SAMPLE_DATA, NESHAN_SERVICE_KEY, NESHAN_TIMEOUT_S, ROUTE_REQUESTS_PER_MINUTE, GEO_REQUESTS_PER_MINUTE, TOOLS_PAID_REQUESTS_PER_MINUTE, REDIS_URL, TRUSTED_PROXY_COUNT, WEB_CONCURRENCY, ADMIN_USERNAME, ADMIN_PASSWORD_HASH (dev: ADMIN_PASSWORD), ADMIN_SECRET_KEY, ADMIN_COOKIE_SECURE, ADMIN_SESSION_MAX_AGE_S, ADMIN_LOGIN_MAX_FAILURES, ADMIN_LOGIN_WINDOW_S, ADMIN_ALLOWED_ORIGINS, TOOLS_ENABLED, TOOLS_API_KEY` — see `.env.example`.

## Production checklist (`APP_ENV=prod`)
The app **refuses to start** (listing every problem, never secret values) unless: PostgreSQL; CORS origins are `https` and not `*` (Capacitor Android's `https://localhost` and `capacitor://localhost` are accepted); `EXPOSE_SAMPLE_DATA=false`; `TOOLS_API_KEY` set while tools are on; `REDIS_URL` set when `WEB_CONCURRENCY>1`; if the admin is configured it uses `ADMIN_PASSWORD_HASH`, a ≥32-char secret and a Secure cookie.

## Steps
1. `python -m app.admin_auth` → put the printed hash in `ADMIN_PASSWORD_HASH`. Generate `ADMIN_SECRET_KEY` and `TOOLS_API_KEY` with `python -c "import secrets;print(secrets.token_urlsafe(48))"`.
2. Create a PostgreSQL database; set `DATABASE_URL=postgresql+psycopg://user:pass@host:5432/harako`.
3. Apply the schema: `alembic upgrade head` (Compose: the `migrate` service runs it before `api`). Run it once per deploy, not from every replica.
4. Load real content (admin panel or `python -m app.seed my_places.json`). Placeholder records are `source=seed-sample`; remove with `python -m app.seed --purge-samples`.
5. Put a TLS-terminating proxy in front (HTTPS). Set `TRUSTED_PROXY_COUNT` to the number of proxies appending `X-Forwarded-For`; keep the proxy's `Host` header intact or list the admin host in `ADMIN_ALLOWED_ORIGINS`.
6. Run: `docker compose up --build -d` (or your orchestrator). Health: `/health/live` (container healthcheck), `/health` (readiness). Logs: uvicorn access log is off in the image; if enabled, coordinates in query strings are redacted.
7. Backups: schedule `pg_dump` of the `harako` database (not provided here); test a restore.
8. Upgrading from a v0.1 dev SQLite file that was created by `create_all`: stamp it instead of migrating: `alembic stamp head`.

## Android (Capacitor, API 24+)
Backend choices are compatible: plain HTTPS JSON, CORS for `https://localhost`. Frontend must be checked once its source is reviewed.
