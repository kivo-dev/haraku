import json
from pathlib import Path


def test_seed_uses_harako_approved_top_level_categories():
    data = json.loads((Path(__file__).parents[1] / "data" / "seed.json").read_text(encoding="utf-8"))
    assert [row["key"] for row in data["categories"]] == [
        "attractions", "accommodation_food", "transport", "public_services", "nature_adventure"
    ]
    allowed = {row["key"] for row in data["categories"]}
    assert all(place["category"] in allowed for place in data["places"])
