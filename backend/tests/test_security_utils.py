import logging

from app.logging_filters import RedactLocationFilter, redact_location
from app.security_utils import origin_allowed


def test_same_origin_is_allowed():
    assert origin_allowed("https://admin.example", None, "admin.example")
    assert origin_allowed("http://localhost:8000", None, "localhost:8000")


def test_cross_origin_is_refused():
    assert not origin_allowed("https://evil.example", None, "admin.example")
    assert not origin_allowed("https://admin.example.evil.io", None, "admin.example")


def test_referer_is_used_when_origin_is_missing_or_null():
    assert origin_allowed(None, "https://admin.example/admin/place/list", "admin.example")
    assert origin_allowed("null", "https://admin.example/admin/", "admin.example")
    assert not origin_allowed("null", "https://evil.example/x", "admin.example")


def test_no_origin_and_no_referer_is_refused():
    assert not origin_allowed(None, None, "admin.example")
    assert not origin_allowed("", "", "admin.example")


def test_extra_hosts_are_honoured():
    assert origin_allowed("https://admin.example", None, "internal:8000", ["admin.example"])
    assert not origin_allowed("https://other.example", None, "internal:8000", ["admin.example"])


def test_redact_location_in_text():
    out = redact_location("GET /v1/route?from_lat=39.2912&from_lng=44.5123&to_place=x HTTP/1.1")
    assert "39.29" not in out and "44.51" not in out
    assert "to_place=x" in out and "from_lat=REDACTED" in out
    assert redact_location("/v1/places?lat=-12.5&lng=3&q=lat") == "/v1/places?lat=REDACTED&lng=REDACTED&q=lat"


def test_filter_redacts_uvicorn_style_args():
    rec = logging.LogRecord("uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
                            ("1.2.3.4:5", "GET", "/v1/places/nearby?lat=39.3&lng=44.5", "1.1", 200), None)
    assert RedactLocationFilter().filter(rec) is True
    assert "39.3" not in rec.getMessage() and "44.5" not in rec.getMessage()
