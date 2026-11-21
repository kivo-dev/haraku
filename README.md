# HARAKO — Project Documentation Pack

**Version:** 0.1 (working draft)  
**Target:** Operational MVP for 3 Azar 1405 (24 November 2026)  
**Scope:** Maku Free Zone, West Azerbaijan, Iran  
**Languages:** Persian and English  
**Platforms:** Responsive Web App first; PWA enhancement where feasible; native mobile apps later

## Documents
- `01_PRD.md` — product definition, users, scope, requirements, acceptance criteria.
- `02_ARCHITECTURE.md` — proposed system architecture, services, APIs, security, deployment.
- `03_DATABASE.md` — initial PostgreSQL/PostGIS data model and provenance strategy.
- `04_SIX_DAY_EXECUTION_PLAN.md` — sprint plan, roles, release gates, risks.

## Important assumptions
1. The official legal/geographic boundary of Maku Free Zone has not yet been supplied or verified. Do not approximate it using Maku city or county boundaries.
2. OSM is an initial source for map data and some POIs, not a guarantee of complete or verified local information.
3. Public OSM tile, Nominatim, and demo routing services are not production infrastructure guarantees. Select a suitable provider or self-host before public launch at meaningful traffic.
4. The six-day delivery target requires a strict MVP. Offline maps, payments, booking, native apps, user reviews, and advanced AI itinerary planning are out of scope.
5. Any operational launch must include real-device testing, privacy notice, clear location permission, visible map attribution, monitoring, backups, and a fallback if map/routing services fail.

## Date note
3 Azar 1405 corresponds to 24 November 2026. From 17 November, this leaves roughly six full working days after today (18–23 November), depending on the team's working calendar. Confirm the event's exact local schedule.
