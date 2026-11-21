# HARAKO — Technical Architecture

**Version:** 0.1 — Proposed MVP architecture

## 1. Architecture principles

- Ship a modular monolith first; avoid microservices under a six-day deadline.
- Keep map rendering, routing, geocoding, and AI behind provider adapters.
- Store HARAKO place records in our own database.
- Keep all secrets and AI orchestration on the server.
- Treat external services as replaceable dependencies.
- Record provenance and verification status for every place.

## 2. Proposed stack

| Layer | MVP choice | Notes |
|---|---|---|
| Web frontend | Next.js + TypeScript | Responsive mobile-first UI |
| Styling | Tailwind CSS | RTL/LTR support must be tested |
| Map rendering | MapLibre GL JS | Provider-neutral renderer |
| Backend | Python + FastAPI | REST API and AI orchestration |
| Database | PostgreSQL + PostGIS | Place search and spatial queries |
| ORM/migrations | SQLAlchemy + Alembic | Team may use existing equivalent |
| Routing | OSRM-compatible provider/instance | Do not assume public demo server is production-ready |
| Geocoding | Database search first; geocoder adapter second | Public Nominatim has strict usage limits |
| AI | LLM provider behind `AIProvider` interface | Tool calling; provider can be changed |
| Deployment | Docker Compose initially | HTTPS reverse proxy and managed backups |

## 3. High-level request flow

Browser → Next.js → FastAPI → PostgreSQL/PostGIS

For map rendering, the browser loads map style/tiles from a selected tile provider and displays OSM attribution where required.

For route requests:
Browser → FastAPI `/routes` → routing provider/OSRM → normalized route response → browser map.

For AI:
Browser → FastAPI `/assistant/chat` → LLM intent/tool selection → internal HARAKO tools → database/routing provider → grounded response.

## 4. Suggested repository structure

```text
harako/
  apps/
    web/
      app/
      components/
      features/
        map/
        places/
        search/
        assistant/
        i18n/
      public/
  services/
    api/
      app/
        api/
        core/
        models/
        schemas/
        services/
          places/
          routing/
          geocoding/
          assistant/
        adapters/
          maps/
          routing/
          llm/
      tests/
  infra/
    docker-compose.yml
    nginx/
  docs/
    01_PRD.md
    02_ARCHITECTURE.md
    03_DATABASE.md
    04_SIX_DAY_EXECUTION_PLAN.md
  .env.example
  README.md
```

If the team already has a working repository or stack, do not rewrite it just to match this proposal. Adapt the architecture to existing working code.

## 5. MVP API contract

Base path: `/api/v1`

### Health
- `GET /health`
- Returns service status and version. Do not expose secrets or internal infrastructure details.

### Places
- `GET /places?query=&category=&lang=&limit=&offset=`
- `GET /places/{place_id}`
- `GET /places/nearby?lat=&lon=&radius_m=&category=&lang=&limit=`

### Categories
- `GET /categories?lang=`

### Routes
- `POST /routes`
- Request:
```json
{
  "origin": {"lat": 39.0, "lon": 44.0},
  "destination": {"lat": 39.1, "lon": 44.1},
  "profile": "driving"
}
```
- Response should normalize provider output:
```json
{
  "distance_m": 1200,
  "duration_s": 240,
  "geometry": {"type": "LineString", "coordinates": []},
  "provider": "configured-provider"
}
```
The sample coordinates are illustrative only, not actual HARAKO destinations.

### Assistant
- `POST /assistant/chat`
- Request:
```json
{
  "message": "Find a nearby place to visit",
  "language": "en",
  "location": {"lat": 39.0, "lon": 44.0}
}
```
- Response:
```json
{
  "answer": "Here are relevant places based on the available data.",
  "places": [],
  "route": null,
  "grounding": {
    "used_tools": ["nearby_places"],
    "data_status": "available"
  }
}
```
The example coordinates are placeholders. Location must be optional and user-authorized.

## 6. Provider interfaces

Implement small interfaces so the product is not coupled to one vendor:

- `TileStyleProvider`: returns style URL/configuration.
- `Geocoder`: `search()` and `reverse()`.
- `RoutingProvider`: `route(origin, destination, profile)`.
- `AIProvider`: `generate_with_tools(messages, tools)`.
- `PlaceRepository`: search, nearby, detail, create/update.

The browser should not call a public geocoding endpoint on every keystroke. Search HARAKO's own indexed place database first.

## 7. Map and OSM operating rules

- OSM data is not the same as the OSM tile service. Data is available under ODbL; comply with attribution and share-alike obligations where applicable.
- If using `tile.openstreetmap.org`, display visible `© OpenStreetMap contributors` attribution, respect caching headers, do not bulk-download/prefetch tiles, and do not promise offline maps.
- Public OSM tile infrastructure is best-effort and has no SLA. For an institutional/commercial launch, choose a provider with suitable terms/SLA or host tiles.
- Do not use public Nominatim as a high-volume production autocomplete service. Its public policy has an absolute maximum of one request per second for the application and disallows certain bulk/systematic uses.
- Do not assume the public OSRM demo server is suitable for production traffic. Use a contracted routing provider or self-hosted instance with suitable data and monitoring.
- Make provider URLs/configuration environment-driven; do not hard-code them across the codebase.

## 8. Security and privacy

- HTTPS in production.
- Keep secrets in environment/secret manager, never in client code.
- Validate coordinate ranges and request sizes.
- Rate-limit `/assistant/chat`, search, and route endpoints.
- Add CORS allowlist for production domains.
- Use parameterized database queries.
- Limit AI tool permissions to read-only MVP tools.
- Do not let the LLM execute arbitrary SQL, shell commands, or unrestricted URLs.
- Avoid logging precise user coordinates or raw sensitive prompts unless necessary; redact or minimize logs.
- Explain geolocation use before requesting permission.
- Provide a privacy notice and contact channel.
- Set database backup and restore procedure before launch.

## 9. Deployment

Minimum:
- One production web deployment.
- One API deployment.
- PostgreSQL with PostGIS.
- HTTPS domain.
- Environment variables for database, AI provider, routing provider, allowed origins.
- Health check and error monitoring.
- Database backup.

Use Docker Compose for a simple single-host deployment if the team has no existing deployment platform. Do not spend the six-day sprint building a complex Kubernetes setup.

## 10. Testing

- Unit tests: place search, validation, language fallback, AI tool validation.
- API tests: health, places, nearby, route errors, assistant no-location flow.
- Integration tests: database spatial query, routing adapter, LLM tool calls.
- Browser tests: mobile viewport, RTL/LTR, QR landing, geolocation denied/granted.
- Field tests: actual phone, actual network, several real routes in the target area.
