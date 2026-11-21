# Neshan integration status

Nothing below was verified against Neshan's official documentation or a real response: the build
sandbox had no network access. **No Neshan URL, header, parameter or response shape was added in
this release.** Only the pre-existing routing adapter remains, still marked unverified.

| Capability | State | Where |
|---|---|---|
| Car routing | unverified (written from memory in v0.1) | `app/services/neshan.py` |
| Pedestrian routing, alternatives | pending | — |
| Geocode / reverse geocode / place search | pending (HTTP 501, final contract) | `app/providers/pending.py` |
| Traffic-aware routing, nearby discovery via Neshan | not investigated | — |
| Browser map SDK (frontend) | not touched; needs the **browser** key, separate from `NESHAN_SERVICE_KEY` | frontend |

## To verify a capability
1. Read the current official docs; note URL, method, auth header, parameters, response, limits, and licence terms on storing/caching.
2. Call it once with your real key from your own machine (`python -m app.services.neshan_check 39.29,44.51 39.39,44.38` prints the raw routing JSON) and keep the raw JSON.
3. Write `app/providers/neshan_<capability>.py` implementing the Protocol in `app/providers/base.py`; add mocked-response tests (success, empty, malformed, HTTP error, timeout).
4. Switch the factory in `app/providers/registry.py` and change that capability's state in `capability_status()`.
5. Confirm the polyline encoding of route geometry, then set `geometry_encoding` accordingly and tell the frontend.

Do not persist or cache Neshan results until the licence explicitly allows it.
