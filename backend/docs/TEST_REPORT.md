# Test report — HARAKO backend v0.2 integration preparation

## Executed in the isolated build environment

### Pytest
Command:
```bash
python -m pytest -q -rs -p no:cacheprovider
```
Result: **96 passed, 0 failed, 1 skipped**.

The skipped test is `tests/test_admin_http.py` because `sqladmin` is not installed in this environment:
`could not import 'sqladmin': No module named 'sqladmin'`.

The Alembic `path_separator` setting was added after the initial run; the final run completed without those deprecation warnings.

### Python syntax
`pytest` imports the backend modules used by the suite successfully. No Python syntax failures were reported.

### Fresh SQLite seed + HTTP smoke test
Using a new SQLite database:
- `python -m app.seed` loaded 4 sample places and 4 sample opportunities.
- `GET /health` → 200
- `GET /v1/categories` → 200 and returned exactly:
  `attractions`, `accommodation_food`, `transport`, `public_services`, `nature_adventure`
- `GET /v1/places` → 200; sample provenance fields were present (`source=seed-sample`, `is_sample=true`).
- `GET /v1/places/maku-viewpoint` → 200
- `GET /v1/suggestions` → 200
- `GET /v1/opportunities` → 200
- `GET /v1/providers/status` → 200

### Alembic
On a separate fresh SQLite database:
`alembic upgrade head` → exit code 0.

## Not verified in this environment

- SQLAdmin HTTP login and cookie behavior: skipped because `sqladmin` was unavailable.
- Docker image build / Docker Compose runtime.
- Real PostgreSQL and Redis services.
- Real Neshan routing response; the car adapter is still explicitly unverified.
- Geocode, reverse geocode and external place search; these adapters intentionally remain pending and return 501.
- Full Next.js typecheck, lint and production build. Only the changed TypeScript/TSX files were syntax-parsed; full dependency-aware typechecking requires the complete frontend checkout and its installed npm dependencies.
- Live browser-to-backend CORS and user-device network testing.

## Interpretation

The backend v0.2 core, migrations, sample seeding, and primary read endpoints passed the checks above. This is not a production-readiness certification. Provider verification, SQLAdmin runtime testing, full frontend build, Docker/PostgreSQL/Redis testing, real regional data and end-to-end browser/device tests remain before final release.
