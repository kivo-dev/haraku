# Changes in v0.2 (on top of v0.1 + admin patch)

## Defects fixed
| # | Problem (v0.1) | Fix |
|---|---|---|
| 1 | No initial Alembic migration; prod had no way to create tables | `migrations/versions/0001_initial_schema.py` + test that it matches the models; `seed` no longer calls `create_all` in prod |
| 3 | Per-process rate limiters (route + admin login) | `app/ratestore.py`: memory or Redis-backed (fixed window), automatic fallback to memory if Redis fails; admin login lockout uses the same store |
| 4 | Admin cookie flags implicit, no CSRF, plaintext password | Explicit cookie: `harako_admin`, HttpOnly, SameSite=Strict, Secure in prod, max-age; fresh session per login; Origin/Referer guard on unsafe `/admin` requests; PBKDF2-SHA256 password hash (`python -m app.admin_auth`) |
| 5 | No production config validation; proxy IP wrong; coordinates in logs | `app/prodcheck.py` (refuses to start in prod); `TRUSTED_PROXY_COUNT` + right-most X-Forwarded-For logic; `/health/live`; coordinate redaction filter; Docker `--no-access-log`, non-root user, healthcheck |
| 6 | Opportunities unpaginated | `limit`/`offset` (defaults keep old behaviour up to 200 rows); `total` = full count |
| 7 | Placeholder data could look real in production | `EXPOSE_SAMPLE_DATA=false` hides `source=seed-sample` everywhere; prod requires it |
| 8 | Missing endpoints | `/places/nearby`, `/geo/*` (501 contract), `/providers/status`, `/tools/*` + manifest |

## Added
Provider abstraction `app/providers/` (Protocols, pending Neshan stubs, registry); shared `services/discovery.py`;
`ToolPlace`/`ToolRoute` AI contracts (`data_source`, `verified`, `is_sample`, null-not-invented);
index `ix_places_lat_lng`; Redis in Compose; `migrate` one-shot service; `requirements-dev.txt`.

## Compatibility
No existing route, parameter or response field was removed or renamed. `/v1/places*`, `/categories`, `/suggestions`, `/route` behave as before
(default `EXPOSE_SAMPLE_DATA=true`). Only visible differences: `/opportunities` now accepts `limit/offset` and `total` is the full count;
`/places/nearby` and new paths exist. CORS is unchanged (`GET`, `allow_headers=*`) until the frontend is reviewed.

## Files
**Created:** `app/{ratestore,security,security_utils,prodcheck,logging_filters,schemas_tools}.py`, `app/providers/{__init__,base,pending,registry}.py`, `app/services/discovery.py`, `app/routers/{geo,system,tools}.py`, `migrations/versions/0001_initial_schema.py`, `requirements-dev.txt`, `docs/*`, `tests/{conftest,test_api,test_tools,test_migrations,test_admin_http,test_ratestore,test_prodcheck,test_admin_hash,test_security_utils}.py`.
**Modified:** `app/{admin,admin_auth,config,constants,db,main,models,ratelimit,seed}.py`, `app/routers/{places,routes,opportunities}.py`, `app/services/neshan.py` (types moved to providers; still UNVERIFIED), `.env.example`, `.gitignore`, `Dockerfile`, `docker-compose.yml`, `requirements.txt` (+redis, −pytest), `README.md`. **Admin patch merged** (`admin.py`, `admin_auth.py`, `test_admin_auth.py` added; its `main/config/models/requirements` changes already contained). **Removed:** none.

## Known limitations
Neshan: everything except car routing is a pending stub; routing itself is unverified. Origin-guard is not a token-based CSRF scheme. Redis limiter is fixed-window. No PostGIS (Python haversine + bounding box is enough at this scale). Official Free Zone boundary not modelled (needs an authoritative source). CORS headers not narrowed. Frontend not yet inspected.
