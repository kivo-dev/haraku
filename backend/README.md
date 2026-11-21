# HARAKO Backend — v0.2

FastAPI · SQLAlchemy 2 · PostgreSQL (SQLite for local development) · Alembic · Docker Compose

## Current integration status
This backend provides the public read API consumed by the HARAKO Next.js frontend:
- `GET /v1/categories`
- `GET /v1/places`, `GET /v1/places/{id}`, `GET /v1/places/nearby`
- `GET /v1/suggestions`
- `GET /v1/opportunities`, `GET /v1/opportunities/{id}`
- `GET /v1/route` (car routing adapter is **unverified** until checked against official Neshan docs / a real response)
- `GET /v1/geo/geocode`, `/reverse`, `/search` (contracts exist; currently return 501 while provider adapters are pending)
- `GET /v1/providers/status`
- `GET /v1/tools/*` (server-to-server AI tools; not a conversational assistant endpoint)
- `/admin` (disabled until valid admin environment variables are configured)
- `/health` (database readiness) and `/health/live` (process liveness)

The frontend base URL is configured with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/v1`.
The backend CORS allow-list must include the browser origin, normally `http://localhost:3000` and/or `http://127.0.0.1:3000`.

## Local development
```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/docs` for the API schema and `http://127.0.0.1:8000/health` for DB readiness.

## Tests
```bash
pytest -q
```
The integration-preparation test run in the build environment completed with **96 passed, 1 skipped**. This does not replace browser-to-API testing on the user's machine, real PostgreSQL/Redis/Docker testing, or Neshan provider verification.

## Docker Compose (backend services)
```bash
cp .env.example .env
docker compose up --build -d
docker compose run --rm api python -m app.seed
```
Compose starts PostgreSQL, Redis, migrations, and the API. Run the Next.js frontend separately from its own project directory.

## Admin panel
The panel is `/admin` and remains disabled until configured.
For local development, set `ADMIN_USERNAME`, `ADMIN_PASSWORD` (at least 10 characters), and `ADMIN_SECRET_KEY` (at least 32 characters) in `.env`.
For production, generate a hash with `python -m app.admin_auth` and use `ADMIN_PASSWORD_HASH`; do not store plaintext production passwords.
Generate the secret with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Sample data and real content
`data/seed.json` contains placeholder examples only. They are marked `source=seed-sample` and are not verified real tourist records. The seed includes HARAKO's five approved top-level categories:
1. `attractions` — جاذبه‌های گردشگری
2. `accommodation_food` — اقامت و پذیرایی
3. `transport` — حمل‌ونقل
4. `public_services` — خدمات عمومی
5. `nature_adventure` — طبیعت و ماجراجویی

Do not present sample content as verified. In production set `EXPOSE_SAMPLE_DATA=false`, import verified regional records, and review each record's coordinates, source, status, and verification state.

## Provider status and limitations
- Neshan car routing is implemented but **unverified**. Do not rely on it in production until the official API endpoint, parameters, authentication, and response format have been checked.
- Geocoding, reverse geocoding, and external place search are explicit pending adapters and return HTTP 501.
- The `/tools` routes expose database/provider tools for a separate assistant service; this backend release does not implement a natural-language chat assistant.
- The official Maku Free Zone legal boundary is not yet modeled. Do not infer the legal boundary from Maku city/county boundaries.
- Tourist accounts and sessions are intentionally out of current release scope. Public browsing stays anonymous; admin access remains protected.
