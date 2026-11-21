"""API tests on a real (temporary SQLite) database."""
ORIGIN = {"lat": 39.30, "lng": 44.50}


def ids(res):
    return [i["id"] for i in res.json()["items"]]


# ---------- existing contract (must not change) ----------
def test_places_list_shape_and_hides_drafts(client, seeded):
    r = client.get("/v1/places")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"items", "total", "limit", "offset"}
    assert "draft" not in ids(r)
    first = body["items"][0]
    for key in ("id", "category", "name", "area", "summary", "lat", "lng", "rating", "distanceKm", "featured", "image", "images", "reason", "verified"):
        assert key in first
    assert set(first["name"]) == {"fa", "en"}


def test_place_detail_and_404(client, seeded):
    assert client.get("/v1/places/near").status_code == 200
    assert client.get("/v1/places/draft").status_code == 404
    assert client.get("/v1/places/nope").status_code == 404


def test_list_with_position_sorts_by_distance(client, seeded):
    r = client.get("/v1/places", params=ORIGIN)
    assert ids(r)[0] in ("near", "sample")
    assert "no-coords" not in ids(r)
    d = [i["distanceKm"] for i in r.json()["items"]]
    assert d == sorted(d)


def test_lat_without_lng_is_422(client, seeded):
    assert client.get("/v1/places", params={"lat": 39.3}).status_code == 422
    assert client.get("/v1/places", params={"radius_km": 5}).status_code == 422


def test_categories_and_suggestions(client, seeded):
    assert [c["key"] for c in client.get("/v1/categories").json()] == ["nature", "history"]
    r = client.get("/v1/suggestions", params={"limit": 3, "seed": 1})
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    assert "draft" not in ids(r)


# ---------- empty database is NOT an error ----------
def test_empty_database_returns_empty_lists(client):
    r = client.get("/v1/places")
    assert r.status_code == 200 and r.json()["items"] == [] and r.json()["total"] == 0
    assert client.get("/v1/places/nearby", params=ORIGIN).json()["items"] == []
    assert client.get("/v1/opportunities").json() == {"items": [], "total": 0}


# ---------- nearby ----------
def test_nearby_sorted_and_radius_limited(client, seeded):
    r = client.get("/v1/places/nearby", params={**ORIGIN, "radius_km": 25})
    assert r.status_code == 200
    got = ids(r)
    assert "far" not in got and "draft" not in got and "no-coords" not in got
    assert got[0] in ("near", "sample")
    d = [i["distanceKm"] for i in r.json()["items"]]
    assert d == sorted(d) and all(x is not None for x in d)


def test_nearby_category_filter(client, seeded):
    assert ids(client.get("/v1/places/nearby", params={**ORIGIN, "radius_km": 50, "category": "history"})) == ["mid"]


def test_nearby_validates_coordinates(client, seeded):
    for bad in ({"lat": 91, "lng": 44}, {"lat": 39, "lng": 181}, {"lat": "abc", "lng": 44}, {"lat": 39}, {"lat": "nan", "lng": 44}, {**ORIGIN, "radius_km": 0}, {**ORIGIN, "radius_km": 5000}):
        assert client.get("/v1/places/nearby", params=bad).status_code == 422, bad


def test_nearby_is_not_shadowed_by_place_id_route(client, seeded):
    assert "items" in client.get("/v1/places/nearby", params=ORIGIN).json()


def test_nearby_pagination(client, seeded):
    page1 = client.get("/v1/places/nearby", params={**ORIGIN, "radius_km": 200, "limit": 1, "offset": 0}).json()
    page2 = client.get("/v1/places/nearby", params={**ORIGIN, "radius_km": 200, "limit": 1, "offset": 1}).json()
    assert page1["total"] == page2["total"] >= 3
    assert page1["items"][0]["id"] != page2["items"][0]["id"]


# ---------- sample data must not silently look real ----------
def test_sample_data_hidden_when_switched_off(client, seeded, settings, monkeypatch):
    assert "sample" in ids(client.get("/v1/places"))
    monkeypatch.setattr(settings, "expose_sample_data", False)
    assert "sample" not in ids(client.get("/v1/places"))
    assert "sample" not in ids(client.get("/v1/places/nearby", params=ORIGIN))
    assert client.get("/v1/places/sample").status_code == 404
    assert [o["id"] for o in client.get("/v1/opportunities").json()["items"]] == ["o1"]
    assert client.get("/v1/opportunities/o-sample").status_code == 404


# ---------- opportunities ----------
def test_opportunities_pagination_and_total(client, seeded):
    r = client.get("/v1/opportunities", params={"limit": 1})
    assert len(r.json()["items"]) == 1 and r.json()["total"] == 2


# ---------- route ----------
def test_route_to_place_and_to_coordinates(client, seeded, fake_routing):
    r = client.get("/v1/route", params={"from_lat": 39.3, "from_lng": 44.5, "to_place": "mid"})
    assert r.status_code == 200 and r.json()["distance_m"] == 1234 and r.json()["provider"] == "fake"
    assert fake_routing.calls[0][1] == (39.40, 44.60)
    assert client.get("/v1/route", params={"from_lat": 39.3, "from_lng": 44.5, "to_lat": 39.4, "to_lng": 44.6}).status_code == 200


def test_route_errors(client, seeded, fake_routing):
    base = {"from_lat": 39.3, "from_lng": 44.5}
    assert client.get("/v1/route", params=base).status_code == 422
    assert client.get("/v1/route", params={**base, "to_place": "nope"}).status_code == 404
    assert client.get("/v1/route", params={**base, "to_place": "no-coords"}).status_code == 422
    assert client.get("/v1/route", params={**base, "to_place": "mid", "mode": "walk"}).status_code == 422
    assert client.get("/v1/route", params={"from_lat": 200, "from_lng": 44.5, "to_place": "mid"}).status_code == 422


def test_route_without_key_is_503(client, seeded):  # real adapter, empty NESHAN_SERVICE_KEY
    r = client.get("/v1/route", params={"from_lat": 39.3, "from_lng": 44.5, "to_place": "mid"})
    assert r.status_code == 503


def test_route_rate_limit(client, seeded, fake_routing, settings, monkeypatch):
    monkeypatch.setattr(settings, "route_requests_per_minute", 2)
    p = {"from_lat": 39.3, "from_lng": 44.5, "to_place": "mid"}
    assert [client.get("/v1/route", params=p).status_code for _ in range(3)] == [200, 200, 429]
    assert client.get("/v1/route", params=p).headers["retry-after"] == "60"


# ---------- geo: contract final, implementation pending ----------
def test_geo_endpoints_answer_501_with_structured_body(client):
    for path, params, cap in (
        ("/v1/geo/geocode", {"q": "ماکو"}, "geocode"),
        ("/v1/geo/reverse", {"lat": 39.3, "lng": 44.5}, "reverse_geocode"),
        ("/v1/geo/search", {"q": "cafe"}, "place_search"),
    ):
        r = client.get(path, params=params)
        assert r.status_code == 501, path
        d = r.json()["detail"]
        assert d["code"] == "provider_not_implemented" and d["provider"] == "neshan" and d["capability"] == cap


def test_geo_validation(client):
    assert client.get("/v1/geo/geocode", params={"q": "a"}).status_code == 422
    assert client.get("/v1/geo/reverse", params={"lat": 99, "lng": 44}).status_code == 422
    assert client.get("/v1/geo/geocode", params={"q": "ماکو", "lat": 39.3}).status_code == 422


def test_geo_rate_limit(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "geo_requests_per_minute", 1)
    assert client.get("/v1/geo/geocode", params={"q": "ماکو"}).status_code == 501
    assert client.get("/v1/geo/geocode", params={"q": "ماکو"}).status_code == 429


# ---------- system ----------
def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/health/live").json() == {"status": "ok"}


def test_provider_status_is_honest_and_has_no_secrets(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "neshan_service_key", "SECRET-VALUE-123")
    r = client.get("/v1/providers/status")
    assert "SECRET-VALUE-123" not in r.text
    caps = {c["capability"]: c for c in r.json()["capabilities"]}
    assert caps["routing_car"]["state"] == "unverified" and caps["routing_car"]["key_configured"] is True
    assert caps["geocode"]["state"] == "pending" and caps["reverse_geocode"]["state"] == "pending"
    assert not any(c["state"] == "verified" and c["provider"] == "neshan" for c in caps.values())


def test_cors_allows_configured_origin_only_for_get(client):
    ok = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    bad = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in bad.headers
    pre = client.options("/v1/places", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    assert pre.status_code == 400
