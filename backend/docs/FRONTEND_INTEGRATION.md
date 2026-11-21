# HARAKO — Frontend / Backend integration handoff

This folder is an integration overlay for the existing Next.js frontend. It does not replace the frontend design or rebuild the app.

## What this integration changes

- Uses the v0.2 FastAPI backend as the source for places, place details, categories, suggestions and economic opportunities.
- Fetches the category list from `GET /v1/categories`; the five approved HARAKO groups are seeded.
- Keeps the API contract bilingual (`fa` / `en`).
- Carries `source` / `is_sample` from backend to frontend, so prototype records can be labeled.
- Fixes null coordinate and null distance handling. A missing coordinate is no longer converted into `0,0`, and an unknown distance is not shown as `0 km`.
- Uses gallery image URLs from the place detail API.
- Stops replacing a successfully returned empty API list with built-in sample records. Sample data is used only when no API URL is configured.
- Adds an explicit frontend `.env.local.example`.

## Apply the backend

1. Make a backup of the current `backend/` directory.
2. Replace the project `backend/` directory with the `backend/` directory in this package. The provided script creates a timestamped backup first.
3. Keep the old `harako.db` inside that backup. The new backend starts with a fresh local SQLite database by default; this avoids silently mixing an older prototype schema/data file with the new integration baseline.
4. In `backend/`, create the local environment:
   ```bash
   cp .env.example .env
   ```
5. Keep `APP_ENV=dev` and `DATABASE_URL=sqlite:///./harako.db` for the first local integration.
6. The local CORS list should include the browser origin, e.g.:
   ```env
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```
7. Install and start:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   alembic upgrade head
   python -m app.seed
   uvicorn app.main:app --reload
   ```
8. Confirm `http://127.0.0.1:8000/health` returns `{"status":"ok"}` and open `http://127.0.0.1:8000/docs`.

## Apply the frontend overlay

Copy the contents of this package's `frontend/` directory into the root of the existing Next.js project, preserving the folder structure. Do not copy it into a nested `frontend/frontend` directory.

Then:
```bash
cp .env.local.example .env.local
npm install
npm run dev
```

The `.env.local` value should be:
```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/v1
```

Open the frontend at `http://localhost:3000`. If you open the frontend from a phone on the same Wi-Fi, `127.0.0.1` points to the phone, not the computer. Use the computer's LAN IP in `.env.local` and add the frontend browser origin to backend `CORS_ORIGINS`.

## Admin panel

The admin panel is available at `http://127.0.0.1:8000/admin` only after configuring:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD` (local development only; at least 10 characters)
- `ADMIN_SECRET_KEY` (at least 32 characters)

For production, generate a hash with `python -m app.admin_auth` and use `ADMIN_PASSWORD_HASH`. Do not put real `.env` files or secrets in Git.

## Database / Docker

The backend `docker-compose.yml` runs PostgreSQL, Redis, Alembic migration and FastAPI. It does not run Next.js. The frontend is started separately using `npm run dev`.

For a fresh local Docker database:
```bash
cd backend
cp .env.example .env
docker compose up --build -d
docker compose run --rm api python -m app.seed
```

Do not point an existing production database at this development Compose file. Back up the database before any migration or category-key migration.

## API connections currently covered

| Frontend capability | Backend endpoint | Status |
|---|---|---|
| Category chips | `GET /v1/categories` | Connected |
| Place list | `GET /v1/places` | Connected |
| Search / category filter | `GET /v1/places?q=&category=` | Connected |
| Place details and gallery | `GET /v1/places/{id}` | Connected |
| Suggestions | `GET /v1/suggestions` | Connected |
| Economic opportunities | `GET /v1/opportunities` | Connected |
| Nearby places | `GET /v1/places/nearby` | API exists; UI wiring remains |
| Route | `GET /v1/route` | API exists; provider unverified; UI wiring remains |
| Interactive map | `/v1/geo/*` | Pending provider adapter and map UI |
| Conversational assistant | `/v1/tools/*` | Tool API exists; this is not a chat endpoint |

## Test status and limitations

The backend test suite after the integration changes: **96 passed, 1 skipped** in the isolated build environment.

Not yet verified here:
- Next.js `npm run typecheck`, `npm run lint`, and `npm run build` against the full working tree (only the changed source files were packaged as an overlay).
- A real browser session connecting to a running API.
- SQLAdmin HTTP login with all optional dependencies installed.
- Docker/PostgreSQL/Redis runtime.
- Real Neshan routing responses and any geocoding/search endpoints.
- Interactive map rendering and the natural-language assistant.

The `/v1/route` adapter is explicitly unverified; `/v1/geo/*` endpoints intentionally return 501 while their provider adapters are pending. Do not describe those features as production-ready until they are verified.

## Important data rule

The seed data is prototype content only. It has no verified real coordinates. Keep `EXPOSE_SAMPLE_DATA=true` only for local development. Before public launch, import validated records across the full Maku Free Zone, retain source/provenance, verify coordinates, and set `EXPOSE_SAMPLE_DATA=false`.
