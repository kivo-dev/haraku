# HARAKO API v0.2 — endpoint reference

Base: `http(s)://HOST/v1` (health checks have no prefix). Interactive docs: `/docs`.
All endpoints are `GET`. Errors use `{"detail": ...}`. Coordinates are WGS84 decimal degrees.

Legend — **stable**: contract final and implemented · **pending**: contract final, answers HTTP 501 until verified against Neshan's official docs · **unverified**: implemented from memory, must be checked.

## Existing website endpoints (contracts unchanged)
| Endpoint | Notes |
|---|---|
| `GET /places?category&q&lat&lng&radius_km&limit&offset` | `limit` 1–200 (default 100). `lat`+`lng` together → sorted by distance, `distanceKm` filled, only places with coordinates. `radius_km` needs `lat`+`lng`. |
| `GET /places/{id}` | Published places only. 404 otherwise. |
| `GET /categories` | |
| `GET /suggestions?limit&lat&lng&exclude&seed` | `Cache-Control: no-store`. |
| `GET /opportunities?sector&q&limit&offset` | **New:** `limit` (default 200, max 500) and `offset`; `total` is now the full count, not the page size. |
| `GET /opportunities/{id}` | |
| `GET /route?from_lat&from_lng&to_place｜to_lat&to_lng&mode=car` | **unverified** (Neshan routing adapter). 503 no key · 502 provider failure · 429 rate limit (`ROUTE_REQUESTS_PER_MINUTE`, per client IP). |

## New: nearby — **stable**
`GET /places/nearby?lat&lng&radius_km=25&category&limit=20&offset=0` → same `PlaceList` shape as `/places`.
`lat` −90..90, `lng` −180..180 (required), `radius_km` 0<r≤200, `limit` 1–100. Nearest first. Position is not stored.

## New: geo (external provider) — **pending** (HTTP 501)
| Endpoint | Params |
|---|---|
| `GET /geo/geocode` | `q` (2–200 chars), optional `lat`+`lng` bias |
| `GET /geo/reverse` | `lat`, `lng` |
| `GET /geo/search` | `q`, optional `lat`+`lng` — external place search, deliberately separate from `/places` |

501 body: `{"detail":{"code":"provider_not_implemented","provider":"neshan","capability":"geocode|reverse_geocode|place_search","message":"..."}}`.
Future results are always `data_source:"external"`, `verified:false`. Rate limit: `GEO_REQUESTS_PER_MINUTE` per IP.

## New: system
* `GET /health` — readiness (database answers). `GET /health/live` — liveness (no DB).
* `GET /v1/providers/status` — capability states `verified|unverified|pending|off`, `key_configured` flag. Calls no provider. Never contains key values.

## New: AI tools — `/v1/tools/*`
Auth: header `X-Tools-Key` = `TOOLS_API_KEY` (required in prod). `TOOLS_ENABLED=false` → 404.
`GET /v1/tools/manifest` returns every tool, inputs, rules and live state.

| Tool | Path | State |
|---|---|---|
| `search_places` | `/tools/search_places?q&category&lat&lng&radius_km&limit≤50&offset` | stable |
| `nearby_places` | `/tools/nearby_places?lat&lng&radius_km&category&limit≤50` | stable |
| `get_place` | `/tools/get_place/{id}` | stable |
| `get_categories` | `/tools/get_categories` | stable |
| `search_opportunities` | `/tools/search_opportunities?sector&q&limit≤50` | stable |
| `get_route` | `/tools/get_route?from_lat&from_lng&to_place｜to_lat&to_lng&mode=car` | unverified |
| `geocode` | `/tools/geocode?q` | pending |
| `reverse_geocode` | `/tools/reverse_geocode?lat&lng` | pending |

`PlaceOut` additionally returns `source` and `is_sample` so the frontend can label prototype records. `OpportunityOut` returns the same provenance fields. `ToolPlace`: `id, category, name{fa,en}, area{fa,en}, summary{fa,en}, coordinates{lat,lng}|null, distance_km|null, rating|null, verified, verification_status, last_verified_at|null, data_source:"harako_db", record_source, is_sample`.
`ToolRoute`: `provider, provider_status, mode, distance_m, duration_s, geometry|null, geometry_encoding:"provider_native_unverified", destination{lat,lng}, destination_place_id|null`.
Rules for the assistant: null = unknown (never invent ratings/hours/prices); `is_sample:true` = placeholder; `data_source:"external"` is never a HARAKO recommendation. Paid-provider tools share one global limit `TOOLS_PAID_REQUESTS_PER_MINUTE`.

## Admin
`/admin` (SQLAdmin). Off until `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` (or dev-only `ADMIN_PASSWORD`) and `ADMIN_SECRET_KEY` (≥32 chars) are valid.
