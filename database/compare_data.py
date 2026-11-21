import json
import csv
from pathlib import Path

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def read_json(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("places", "data", "features", "items"):
            if isinstance(data.get(key), list):
                return data[key]
    return []

osm = read_csv("osm_review.csv")
v02_csv = read_csv("harako_places_v0.2.csv")
v02_json = read_json("harako_places_v0.2.json")

def get_name(record):
    for key in ("name", "name_fa", "name_en", "title"):
        value = record.get(key)
        if isinstance(value, dict):
            value = value.get("fa") or value.get("en")
        if value and str(value).strip():
            return str(value).strip().casefold()
    return ""

osm_names = {get_name(x) for x in osm if get_name(x)}
csv_names = {get_name(x) for x in v02_csv if get_name(x)}
json_names = {get_name(x) for x in v02_json if get_name(x)}

print("===== HARAKO DATA COMPARISON =====")
print("OSM review records:", len(osm))
print("Version 0.2 CSV records:", len(v02_csv))
print("Version 0.2 JSON records:", len(v02_json))
print()
print("Named OSM records:", len(osm_names))
print("Named v0.2 CSV records:", len(csv_names))
print("Named v0.2 JSON records:", len(json_names))
print()
print("Exact name matches OSM <-> CSV:", len(osm_names & csv_names))
print("Exact name matches OSM <-> JSON:", len(osm_names & json_names))
print("Exact name matches CSV <-> JSON:", len(csv_names & json_names))
print()
print("Note: name matching is preliminary; spelling variants and duplicates may remain.")
