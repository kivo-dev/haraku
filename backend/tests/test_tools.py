"""AI tool endpoints: stable contract for the separately developed assistant."""
KEY = "tools-key-for-tests-123456"


def test_manifest_lists_all_required_tools(client):
    m = client.get("/v1/tools/manifest").json()
    names = {t["name"] for t in m["tools"]}
    assert names == {"search_places", "nearby_places", "get_place", "get_route", "get_categories", "search_opportunities", "geocode", "reverse_geocode"}
    st = {t["name"]: t["state"] for t in m["tools"]}
    assert st["search_places"] == "verified" and st["geocode"] == "pending" and st["get_route"] in ("unverified", "off")


def test_search_places_shape(client, seeded):
    r = client.get("/v1/tools/search_places", params={"q": "near"})
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert item["data_source"] == "harako_db" and item["verified"] is True
    assert item["coordinates"] == {"lat": 39.3, "lng": 44.5} and item["distance_km"] is None
    assert set(item["name"]) == {"fa", "en"} and item["is_sample"] is False


def test_unknown_values_are_null_not_invented(client, seeded):
    item = client.get("/v1/tools/get_place/no-coords").json()
    assert item["coordinates"] is None and item["rating"] is None and item["distance_km"] is None


def test_sample_records_are_flagged(client, seeded):
    assert client.get("/v1/tools/get_place/sample").json()["is_sample"] is True


def test_nearby_tool_has_distances_sorted(client, seeded):
    items = client.get("/v1/tools/nearby_places", params={"lat": 39.3, "lng": 44.5, "radius_km": 30}).json()["items"]
    d = [i["distance_km"] for i in items]
    assert d and d == sorted(d)


def test_tool_validation(client, seeded):
    assert client.get("/v1/tools/nearby_places", params={"lat": 99, "lng": 44}).status_code == 422
    assert client.get("/v1/tools/search_places", params={"lat": 39}).status_code == 422
    assert client.get("/v1/tools/get_place/nope").status_code == 404


def test_categories_and_opportunities_tools(client, seeded):
    assert len(client.get("/v1/tools/get_categories").json()) == 2
    assert client.get("/v1/tools/search_opportunities", params={"sector": "trade"}).json()["total"] == 2


def test_route_tool_reports_provider_status(client, seeded, fake_routing, settings, monkeypatch):
    monkeypatch.setattr(settings, "neshan_service_key", "x")
    r = client.get("/v1/tools/get_route", params={"from_lat": 39.3, "from_lng": 44.5, "to_place": "mid"})
    assert r.status_code == 200
    b = r.json()
    assert b["provider_status"] == "unverified" and b["destination_place_id"] == "mid" and b["geometry_encoding"] == "provider_native_unverified"


def test_geocode_tools_are_501(client):
    assert client.get("/v1/tools/geocode", params={"q": "ماکو"}).status_code == 501
    assert client.get("/v1/tools/reverse_geocode", params={"lat": 39.3, "lng": 44.5}).status_code == 501


def test_tools_key_required_when_configured(client, seeded, settings, monkeypatch):
    monkeypatch.setattr(settings, "tools_api_key", KEY)
    assert client.get("/v1/tools/get_categories").status_code == 401
    assert client.get("/v1/tools/get_categories", headers={"X-Tools-Key": "wrong"}).status_code == 401
    assert client.get("/v1/tools/get_categories", headers={"X-Tools-Key": KEY}).status_code == 200


def test_tools_can_be_disabled(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "tools_enabled", False)
    assert client.get("/v1/tools/manifest").status_code == 404


def test_tools_paid_limit_is_global(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "tools_paid_requests_per_minute", 1)
    assert client.get("/v1/tools/geocode", params={"q": "ماکو"}).status_code == 501
    assert client.get("/v1/tools/reverse_geocode", params={"lat": 1, "lng": 1}).status_code == 429
