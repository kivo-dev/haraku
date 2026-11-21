import json
import csv
from pathlib import Path

source = Path("osm_raw.geojson")
output = Path("osm_review.csv")

with source.open("r", encoding="utf-8") as f:
    data = json.load(f)

def get_coordinates(geometry):
    if not geometry:
        return None, None, "missing"

    coords = []

    def collect(value):
        if isinstance(value, list):
            if len(value) >= 2 and all(
                isinstance(x, (int, float)) for x in value[:2]
            ):
                coords.append((value[0], value[1]))
            else:
                for item in value:
                    collect(item)

    if geometry.get("type") == "Point":
        lon, lat = geometry["coordinates"][:2]
        return lat, lon, "point"

    collect(geometry.get("coordinates"))

    if not coords:
        return None, None, "missing"

    lon = sum(p[0] for p in coords) / len(coords)
    lat = sum(p[1] for p in coords) / len(coords)

    return lat, lon, "approximate"

def classify(tags):
    if tags.get("tourism") or tags.get("historic"):
        return "جاذبه‌های گردشگری"

    if tags.get("natural") or tags.get("leisure") in (
        "nature_reserve", "park", "camp_site"
    ):
        return "طبیعت و ماجراجویی"

    if tags.get("tourism") in ("hotel", "motel", "hostel", "guest_house"):
        return "اقامت و پذیرایی"

    if tags.get("amenity") in (
        "restaurant", "cafe", "fast_food", "food_court"
    ):
        return "اقامت و پذیرایی"

    if tags.get("amenity") in (
        "bus_station", "taxi", "parking"
    ):
        return "حمل‌ونقل"

    if tags.get("highway") in ("bus_stop",):
        return "حمل‌ونقل"

    return "خدمات عمومی"

rows = []

for feature in data.get("features", []):
    tags = feature.get("properties", {})
    osm_id = tags.get("@id", feature.get("id", ""))
    name = (
        tags.get("name")
        or tags.get("name:fa")
        or tags.get("name:en")
        or ""
    )

    lat, lon, method = get_coordinates(feature.get("geometry"))

    rows.append({
        "osm_id": osm_id,
        "name": name,
        "category": classify(tags),
        "latitude": lat,
        "longitude": lon,
        "coordinate_method": method,
        "amenity": tags.get("amenity", ""),
        "tourism": tags.get("tourism", ""),
        "shop": tags.get("shop", ""),
        "historic": tags.get("historic", ""),
        "natural": tags.get("natural", ""),
        "leisure": tags.get("leisure", ""),
    })

fields = list(rows[0].keys()) if rows else []

with output.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(f"Done! {len(rows)} records exported to {output}")
print(f"Named records: {sum(bool(r['name']) for r in rows)}")
print(f"Missing coordinates: {sum(r['latitude'] is None for r in rows)}")
