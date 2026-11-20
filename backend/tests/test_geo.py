import pytest

from app.geo import bounding_box, haversine_km


def test_zero_and_known_distance():
    assert haversine_km(39.3, 44.5, 39.3, 44.5) == 0
    # one degree of latitude is about 111.2 km
    assert haversine_km(39.0, 44.5, 40.0, 44.5) == pytest.approx(111.2, abs=0.5)


def test_symmetric():
    a = haversine_km(39.29, 44.51, 39.39, 44.38)
    b = haversine_km(39.39, 44.38, 39.29, 44.51)
    assert a == pytest.approx(b)


def test_bounding_box_contains_circle_points():
    lat, lng, r = 39.3, 44.5, 20
    min_lat, max_lat, min_lng, max_lng = bounding_box(lat, lng, r)
    # a point exactly r km north / east must be inside (or on the edge of) the box
    assert min_lat < lat < max_lat and min_lng < lng < max_lng
    north = (lat + 0.99 * r / 111.19, lng)  # just inside the circle
    assert haversine_km(lat, lng, *north) == pytest.approx(0.99 * r, abs=0.2)
    assert north[0] <= max_lat + 1e-6
