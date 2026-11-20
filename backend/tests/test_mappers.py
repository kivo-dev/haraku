from types import SimpleNamespace as NS

from app.mappers import opportunity_to_out, place_to_out


def row(**kw):
    base = dict(id="x", category_key="nature", name_fa="ماکو", name_en="", area_fa="", area_en="Maku", summary_fa="", summary_en="",
                lat=None, lng=None, rating=None, featured=False, image_url=None, verification="unverified", images=[])
    base.update(kw)
    return NS(**base)


def test_empty_language_is_filled_from_the_other():
    out = place_to_out(row())
    assert out.name.fa == "ماکو" and out.name.en == "ماکو"
    assert out.area.fa == "Maku" and out.area.en == "Maku"


def test_shape_matches_frontend_expectations():
    out = place_to_out(row(lat=39.3, lng=44.5, featured=True, verification="verified"), distance_km=12.345, reason="near").model_dump()
    assert out["distanceKm"] == 12.3 and out["lat"] == 39.3 and out["featured"] is True and out["verified"] is True
    assert out["reason"] == {"fa": "نزدیک شما", "en": "Near you"}
    assert out["image"] is None and out["images"] == []


def test_detail_includes_gallery():
    out = place_to_out(row(images=[NS(url="/a.jpg"), NS(url="/b.jpg")]), detail=True)
    assert out.images == ["/a.jpg", "/b.jpg"]


def test_opportunity():
    o = opportunity_to_out(NS(id="o", sector="trade", title_fa="الف", title_en="A", summary_fa="", summary_en="", image_url="", verification="verified"))
    assert o.sector == "trade" and o.image is None and o.verified is True
