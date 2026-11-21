# HARAKO — Product Requirements Document (PRD)

**Version:** 0.1 — Draft for team review  
**Date:** 17 November 2026  
**Release target:** 3 Azar 1405 (24 November 2026)

## 1. Product summary

HARAKO is a bilingual smart tourism companion for visitors to the **entire Maku Free Zone operational area**, not only Maku city. It helps domestic and international visitors discover places, understand local services, and navigate to destinations through a mobile-first web experience.

A visitor scans a QR code at an approved point, opens the web app, chooses Persian or English, optionally shares their location, searches or asks the AI assistant for help, reviews real place information, and opens a route.

## 2. Product vision

Make exploring the Maku Free Zone easier, safer, and more understandable for visitors through one reliable digital companion.

## 3. Target users

- Domestic tourists.
- International tourists.
- Visitors arriving for events, business, or shopping.
- Local residents (secondary user group).
- HARAKO content administrators.
- Future institutional stakeholders, including the Maku Free Zone Organization.

## 4. Geographic scope and boundary policy

The product's intended coverage is the whole Maku Free Zone. Three geographic concepts must remain separate in the system:

1. **Official free-zone boundary:** the legally/administratively confirmed polygon supplied by an authoritative source.
2. **Operational coverage:** the area in which HARAKO currently provides usable data and features.
3. **Tourism discovery radius:** nearby places that may be useful even if they are outside the official boundary.

Do not infer the official free-zone polygon from Maku city, Maku County, or an approximate bounding box. Until verified, label coverage as provisional and avoid claims that every part of the region is fully covered.

## 5. Platforms and languages

- Responsive web application, optimized for mobile browsers.
- PWA installation prompt/manifest only if time and testing permit.
- Native Android/iOS applications are future phases.
- Persian and English from the first release.
- All user-facing strings must be localized; Persian layout must support RTL and English LTR.
- Store canonical content separately from translations.

## 6. Core user journey

1. Visitor scans a HARAKO QR code.
2. QR destination opens the web app (no app-store installation required).
3. Visitor selects Persian or English.
4. App explains why location access is useful and requests browser permission only after user action.
5. Map opens centered on the visitor if permission is granted; otherwise it opens on a safe default area/region view.
6. Visitor searches by name/category or opens a place from the map.
7. Place details show available description, category, coordinates, source/verification status, and navigation action.
8. Visitor can ask the AI assistant a natural-language question.
9. AI uses approved backend tools to retrieve places and route data; it does not invent availability, opening hours, distances, or facts.
10. Visitor opens the selected route.

## 7. MVP scope — must have

### P0: release blockers
- Public HTTPS URL and mobile-responsive web app.
- Persian/English language switch.
- Map view with visible OpenStreetMap attribution when OSM data/tiles are used.
- User location flow with explicit permission and graceful denial handling.
- Search of the HARAKO places database.
- Basic place categories and place details.
- Route calculation/display for supported travel mode(s), with clear failure message.
- Seeded, reviewed list of high-priority places.
- QR code linking to the canonical web URL.
- AI assistant limited to grounded tools: search places, nearby places, place details, and route request.
- Privacy notice explaining location use and data handling.
- Basic error logging, uptime check, and backup of the database.

### P1: include only if P0 is stable
- PWA installability.
- Category filters and map markers.
- Basic “near me” suggestions.
- Simple admin interface for creating/editing places.
- Shareable place links.

### Out of scope for the six-day release
- Native Android/iOS applications.
- Offline map downloads.
- Booking, reservations, payments, or ticketing.
- User-generated reviews and ratings.
- Complex itinerary optimizer.
- Image recognition, live translation, voice assistant.
- User accounts unless a real MVP requirement emerges.
- Full coverage guarantee for every village, road, and point of interest.

## 8. AI assistant behavior and guardrails

The AI assistant is an interface to verified tools, not the source of geographic truth.

Allowed initial tools:
- `search_places(query, language, category?, limit?)`
- `nearby_places(lat, lon, radius_m, category?, limit?)`
- `get_place(place_id, language)`
- `get_route(origin, destination, profile)`

Rules:
- The backend validates all coordinates, radius, IDs, and limits.
- The assistant must distinguish verified facts from missing data.
- If location permission is denied, ask the user to select a starting point or search by area.
- Never fabricate opening hours, phone numbers, prices, safety claims, or travel times.
- If no suitable verified place is found, say so and offer a broader search.
- Do not send precise location to an LLM unless needed; prefer backend-side tool execution and send only the minimum context.
- Keep API keys server-side.

## 9. Place data quality

Every place record should include:
- Unique internal ID.
- Name in at least one language.
- Category.
- Latitude/longitude.
- Data source and source reference where available.
- Verification status: `unverified`, `reviewed`, `official`, `rejected`.
- Last checked timestamp.
- Optional address, description, phone, website, opening hours, accessibility details, and image attribution.

Do not represent OSM-imported data as officially verified. Preserve source attribution and license obligations. Local editorial additions should have their own provenance.

## 10. Non-functional requirements

- Mobile-first layout; usable at 360px width and above.
- Initial core interface should remain usable on slower mobile connections.
- API responses should be bounded and paginated where appropriate.
- Validate and sanitize all user input.
- Rate-limit public endpoints and AI requests.
- HTTPS only in production.
- No secrets in frontend bundles or source control.
- Graceful degradation when geolocation, geocoding, map tiles, routing, or AI provider is unavailable.
- Accessibility: readable contrast, keyboard focus, semantic controls, and clear language labels.

## 11. Success criteria for event release

A release candidate is acceptable when:
- QR code opens the correct HTTPS URL on at least two real phones.
- Persian and English navigation work across all MVP pages.
- Map loads and attribution is visible.
- Location permission grant and denial paths both work.
- At least 30–50 priority places have been manually reviewed (target, not a claim of full coverage).
- Search returns expected seeded places.
- A route can be calculated for a tested origin/destination pair and failure is handled.
- AI answers at least five scripted test prompts using real backend data without inventing facts.
- No critical/high-severity security or data-loss issue remains open.
- The team has a fallback demo path if external map/routing services are unavailable.

## 12. Open questions

- Official free-zone boundary source and file format.
- Event venue, expected concurrent users, and network conditions.
- Hosting provider and domain.
- Which travel modes are required at launch: driving, walking, or both.
- Which places are priority for the event.
- Whether an organization contact can validate POIs and official descriptions.
- Privacy policy owner/contact and retention policy.
