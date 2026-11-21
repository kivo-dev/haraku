# HARAKO — Six-Day Execution Plan

**Target date:** 3 Azar 1405 (24 November 2026)  
**Working sprint:** 18–23 November 2026  
**Release:** Operational MVP for event use

## 1. Delivery strategy

The deadline is aggressive. Prioritize one complete end-to-end visitor journey over many partially built features.

Release must demonstrate:
QR → bilingual web app → map → place search/detail → route → grounded AI recommendation.

If a feature threatens the P0 path, defer it.

## 2. Sprint backlog

### Day 1 — 18 Nov: Scope lock and foundations
**Product/Tech**
- Confirm event venue, target user flow, domain, hosting, and deployment owner.
- Confirm official boundary data request owner; if unavailable, label working coverage provisional.
- Freeze P0 requirements.
- Create repository, branch rules, issue board, `.env.example`.
- Bootstrap Next.js, FastAPI, PostgreSQL/PostGIS, Docker Compose.
- Agree API contracts and design tokens.

**Exit criteria**
- Web and API run locally.
- Database connects.
- `/health` passes.
- Team has named owners for each workstream.

### Day 2 — 19 Nov: Map and place data
- Integrate MapLibre and selected tile/style provider.
- Show visible attribution.
- Add language switch and RTL/LTR foundation.
- Create categories and places schema/migrations.
- Import a small initial OSM-derived dataset from a permitted extract/source.
- Manually review priority locations.
- Add place markers and place details.

**Exit criteria**
- Map loads on a real phone.
- At least 30 priority places are in the database, if source data supports it.
- Each imported record has provenance and verification status.

### Day 3 — 20 Nov: Search and location
- Implement place search and category filters.
- Implement geolocation permission flow.
- Implement nearby places using PostGIS.
- Add no-location fallback (manual search/map selection).
- Add loading, empty, and error states.

**Exit criteria**
- Search returns seeded records.
- Nearby query works with valid coordinates.
- Denied location permission does not block the app.

### Day 4 — 21 Nov: Routing and QR
- Integrate routing adapter and selected provider/instance.
- Render route geometry and distance/duration if returned by provider.
- Add route failure fallback.
- Generate canonical QR code pointing to HTTPS production URL.
- Add place share/deep links if time allows.

**Exit criteria**
- At least five real origin/destination test pairs work.
- QR opens the production or staging app on two phones.
- No unsupported claim about route accuracy.

### Day 5 — 22 Nov: AI and admin
- Implement limited tool-calling assistant.
- Tools: search places, nearby places, place detail, route.
- Add guardrails against fabricated facts.
- Add minimal admin CRUD or a controlled seed/import workflow.
- Test five Persian and five English prompts.

**Exit criteria**
- AI responses cite/identify retrieved place records in the UI or response metadata.
- No fabricated opening hours, price, or travel time in scripted tests.
- Admin/editor can correct a place record.

### Day 6 — 23 Nov: QA, field test, release candidate
- Test on real Android and iOS browsers where available.
- Test Persian RTL and English LTR.
- Test location granted/denied, slow network, routing failure, AI failure.
- Verify OSM attribution and provider terms.
- Check HTTPS, secrets, rate limits, backups, privacy notice.
- Fix critical bugs; freeze features.
- Prepare event demo script and fallback screenshots/video.

**Exit criteria**
- P0 acceptance criteria pass.
- No critical/high-severity known defect.
- Production URL and QR are verified.
- Team has a fallback if external map/routing/AI service fails.

## 3. Workstream ownership

| Workstream | Suggested owner |
|---|---|
| Technical architecture and integration | Lead Developer (you) |
| Web UI and responsive behavior | Frontend developer |
| API, database, spatial queries | Backend developer |
| POI collection and verification | GIS/data owner + local reviewers |
| UX and bilingual content | Designer/content owner |
| Test plan and device testing | QA + all developers |
| Event coordination and official data request | Product/event lead |

One person may own multiple workstreams. Name an accountable owner for each.

## 4. P0 acceptance checklist

- [ ] QR opens correct HTTPS web app.
- [ ] App works without account creation.
- [ ] Persian/English switching works.
- [ ] Map renders with visible attribution.
- [ ] Geolocation is opt-in and denial is handled.
- [ ] Place search works against HARAKO database.
- [ ] Place details show only known data.
- [ ] Route can be displayed for tested routes.
- [ ] AI uses backend tools and does not invent place facts.
- [ ] Error states exist for map, routing, and AI failures.
- [ ] Privacy notice is visible.
- [ ] Production secrets are not exposed.
- [ ] Database backup exists and restore path is known.
- [ ] Real-device smoke test completed.

## 5. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| No official boundary file | Coverage ambiguity | Provisional label; request official GIS polygon |
| Incomplete OSM POIs | Poor discovery | Curate a priority POI list manually |
| Public tile service throttling | Map unavailable | Provider adapter; suitable tile provider/self-host |
| Public geocoder limits | Search failures | Search local DB; geocode only missing records |
| Public routing demo limits | Route failure | Contracted provider or self-hosted OSRM |
| AI hallucination | Misleading guidance | Tool-only grounding; no invented facts |
| Poor mobile internet | Slow app | Small payloads, graceful loading, fallback UI |
| Scope creep | Missed deadline | Freeze P0; defer P1/P2 |

## 6. Release-day policy

Do not call the system fully operational if:
- the map provider has no suitable production terms/availability,
- core routes fail in field tests,
- the place database is mostly unverified,
- no privacy notice exists,
- the production domain/HTTPS is not working.

In that case, present it honestly as a controlled pilot/beta and limit the audience.
