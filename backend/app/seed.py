"""Load content from a JSON file into the database (insert or update by id).

    python -m app.seed                      # uses data/seed.json
    python -m app.seed my_places.json
    python -m app.seed --purge-samples      # delete everything marked source "seed-sample"

This is the way to enter places until the admin panel exists: edit the JSON, run the command again.
The records in data/seed.json are PLACEHOLDERS copied from the frontend prototype (no coordinates,
no real facts). Replace them with real, checked data and purge the samples before going public.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from .config import get_settings
from .db import SessionLocal, init_db
from .models import Category, Opportunity, Place, PlaceImage
from .search_text import build_search_fields

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "data" / "seed.json"
SAMPLE = "seed-sample"


def _upsert_place(db: Session, d: dict) -> None:
    p = db.get(Place, d["id"]) or Place(id=d["id"])
    name, area, summary = d["name"], d.get("area", {}), d.get("summary", {})
    p.category_key = d["category"]
    p.name_fa, p.name_en = name.get("fa", ""), name.get("en", "")
    p.area_fa, p.area_en = area.get("fa", ""), area.get("en", "")
    p.summary_fa, p.summary_en = summary.get("fa", ""), summary.get("en", "")
    p.lat, p.lng = d.get("lat"), d.get("lng")
    p.rating = d.get("rating")
    p.featured = bool(d.get("featured", False))
    p.status = d.get("status", "published")
    p.verification = d.get("verification", "unverified")
    p.source = d.get("source", "manual")
    p.image_url = d.get("image")
    if d.get("verification") == "verified":
        p.last_verified_at = datetime.now(timezone.utc)
    p.search_text, p.search_compact = build_search_fields(
        p.name_fa, p.name_en, p.area_fa, p.area_en, p.summary_fa, p.summary_en
    )
    if "images" in d:
        p.images = [PlaceImage(url=u, sort=i) for i, u in enumerate(d["images"])]
    db.add(p)


def _upsert_opportunity(db: Session, d: dict) -> None:
    o = db.get(Opportunity, d["id"]) or Opportunity(id=d["id"])
    title, summary = d["title"], d.get("summary", {})
    o.sector = d["sector"]
    o.title_fa, o.title_en = title.get("fa", ""), title.get("en", "")
    o.summary_fa, o.summary_en = summary.get("fa", ""), summary.get("en", "")
    o.image_url = d.get("image")
    o.status = d.get("status", "published")
    o.verification = d.get("verification", "unverified")
    o.source = d.get("source", "manual")
    o.search_text, o.search_compact = build_search_fields(o.title_fa, o.title_en, o.summary_fa, o.summary_en)
    db.add(o)


def load(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    if get_settings().app_env != "prod":  # in prod the schema comes from `alembic upgrade head` only
        init_db()
    with SessionLocal() as db:
        for i, c in enumerate(data.get("categories", [])):
            row = db.get(Category, c["key"]) or Category(key=c["key"])
            row.title_fa, row.title_en, row.sort = c["title"]["fa"], c["title"]["en"], c.get("sort", i)
            db.add(row)
        db.flush()
        # Migrate legacy prototype category keys to HARAKO's approved five groups.
        # This is data-only: no records are deleted, and each old key is mapped explicitly.
        legacy_categories = {
            "nature": "nature_adventure",
            "history": "attractions",
            "services": "public_services",
        }
        for old_key, new_key in legacy_categories.items():
            if db.get(Category, new_key) is not None and db.get(Category, old_key) is not None:
                db.execute(update(Place).where(Place.category_key == old_key).values(category_key=new_key))
                db.execute(delete(Category).where(Category.key == old_key))
        db.flush()
        known = set(db.scalars(select(Category.key)))
        for d in data.get("places", []):
            if d["category"] not in known:
                sys.exit(f'Place "{d["id"]}": unknown category "{d["category"]}" (add it under "categories")')
            _upsert_place(db, d)
        for d in data.get("opportunities", []):
            _upsert_opportunity(db, d)
        db.commit()
    print(f'Loaded {len(data.get("places", []))} places, {len(data.get("opportunities", []))} opportunities from {path}')


def purge_samples() -> None:
    with SessionLocal() as db:
        ids = list(db.scalars(select(Place.id).where(Place.source == SAMPLE)))
        if ids:
            db.execute(delete(PlaceImage).where(PlaceImage.place_id.in_(ids)))
        n1 = db.execute(delete(Place).where(Place.source == SAMPLE)).rowcount
        n2 = db.execute(delete(Opportunity).where(Opportunity.source == SAMPLE)).rowcount
        db.commit()
    print(f"Deleted {n1} sample places and {n2} sample opportunities")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--purge-samples"]:
        purge_samples()
    else:
        load(Path(args[0]) if args else DEFAULT_FILE)
