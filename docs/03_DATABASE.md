# HARAKO — Database Design (PostgreSQL + PostGIS)

**Version:** 0.1 — Initial MVP schema proposal

## 1. Design goals

- Support multiple regions in the future.
- Distinguish official boundaries from actual operational coverage.
- Store bilingual content without duplicating core place records.
- Preserve source and verification history.
- Support spatial search with PostGIS.
- Avoid treating imported OSM data as officially verified.

## 2. Core entities

### `regions`
- `id` UUID primary key
- `code` unique text
- `name` text
- `region_type` text (`free_zone`, `city`, `county`, etc.)
- `official_boundary` geometry(MultiPolygon, 4326), nullable until verified
- `boundary_source_id` UUID nullable
- `boundary_status` text (`unknown`, `provisional`, `official`)
- `created_at`, `updated_at`

### `categories`
- `id` UUID primary key
- `code` unique text
- `icon_key` text nullable
- `sort_order` integer
- `is_active` boolean

### `category_translations`
- `category_id` FK
- `language_code` (`fa`, `en`)
- `name` text
- composite primary key (`category_id`, `language_code`)

### `places`
- `id` UUID primary key
- `region_id` FK nullable (nullable for nearby external places)
- `category_id` FK
- `name` text
- `location` geography(Point, 4326)
- `address` text nullable
- `phone` text nullable
- `website_url` text nullable
- `verification_status` text (`unverified`, `reviewed`, `official`, `rejected`)
- `visibility_status` text (`draft`, `published`, `hidden`)
- `is_accessible` boolean nullable
- `created_at`, `updated_at`, `last_verified_at` nullable

### `place_translations`
- `id` UUID primary key
- `place_id` FK
- `language_code` (`fa`, `en`)
- `display_name` text nullable
- `description` text nullable
- `short_description` text nullable
- unique (`place_id`, `language_code`)

### `place_sources`
- `id` UUID primary key
- `place_id` FK
- `source_type` text (`osm`, `official`, `local_editorial`, `business_submission`, `other`)
- `source_name` text
- `source_reference` text nullable (e.g. OSM object type/id or official document reference)
- `license_name` text nullable
- `attribution_text` text nullable
- `retrieved_at` timestamptz
- `notes` text nullable

### `opening_hours`
- `id` UUID primary key
- `place_id` FK
- `day_of_week` smallint (1–7)
- `opens_at` time nullable
- `closes_at` time nullable
- `is_closed` boolean default false
- `source_id` FK nullable
- `verified_at` timestamptz nullable

### `place_media`
- `id` UUID primary key
- `place_id` FK
- `media_url` text
- `caption` text nullable
- `credit` text nullable
- `license_name` text nullable
- `source_url` text nullable

### `qr_codes`
- `id` UUID primary key
- `code` unique text
- `label` text
- `placement_description` text nullable
- `target_path` text
- `is_active` boolean
- `created_at` timestamptz

### `users` (optional for MVP)
- `id` UUID primary key
- `preferred_language` text
- `created_at` timestamptz
Do not require accounts for basic map/search use.

### `favorites` (future)
- `user_id` FK
- `place_id` FK
- composite primary key (`user_id`, `place_id`)

## 3. Spatial indexes and queries

Use PostGIS and create a GiST index on `places.location`.

Nearby query example:
```sql
SELECT id, name,
       ST_Distance(location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS distance_m
FROM places
WHERE visibility_status = 'published'
  AND ST_DWithin(
    location,
    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
    :radius_m
  )
ORDER BY distance_m
LIMIT :limit;
```

Validate latitude (-90 to 90), longitude (-180 to 180), radius upper bound, and maximum result limit in the API.

## 4. Search

For the six-day MVP:
- Use PostgreSQL full-text search or `pg_trgm` for name matching.
- Search both canonical names and translated names.
- Search categories and common spelling variants where practical.
- Avoid depending on public Nominatim for every search keystroke.

## 5. Data provenance and verification

A place may have multiple sources. Do not overwrite provenance when a record is updated.

Suggested statuses:
- `unverified`: imported or entered but not checked.
- `reviewed`: checked by HARAKO editor against a reasonable source.
- `official`: explicitly confirmed by an authorized institution/source.
- `rejected`: inaccurate, duplicate, or unsuitable.

Only `reviewed` and `official` records should be used for strong factual claims. `unverified` places can be shown with a suitable caveat if the product team chooses.

## 6. Data import pipeline

1. Obtain the confirmed region polygon or a clearly labeled provisional working area.
2. Extract relevant OSM features from a suitable extract/provider; do not scrape public tile servers.
3. Map OSM tags to HARAKO categories.
4. Normalize names and coordinates.
5. Deduplicate by source reference and spatial/name similarity.
6. Insert source provenance and license attribution.
7. Mark imported records `unverified`.
8. Manually review priority POIs.
9. Publish reviewed records.

## 7. Important licensing note

OpenStreetMap data is distributed under ODbL. Preserve attribution and assess share-alike obligations for database distribution/derivative databases before a commercial or institutional sale. Keep a record of the exact extract date, source, license, and transformations. Seek legal review before transferring a database built from OSM data to an organization.
