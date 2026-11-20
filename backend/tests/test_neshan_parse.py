import pytest

pytest.importorskip("httpx")  # the adapter needs httpx; skipped on machines without it
from app.services.neshan import ProviderError, _parse  # noqa: E402

SAMPLE = {"routes": [{"overview_polyline": {"points": "abc"}, "legs": [{"distance": {"value": 1234.4}, "duration": {"value": 99.6}}]}]}


def test_parse_ok():
    r = _parse(SAMPLE, "car")
    assert (r.distance_m, r.duration_s, r.geometry, r.provider) == (1234, 100, "abc", "neshan")


@pytest.mark.parametrize("bad", [{}, {"routes": []}, {"routes": [{"legs": []}]}, {"routes": [{"legs": [{"distance": 5}]}]}])
def test_parse_rejects_unknown_shapes(bad):
    with pytest.raises(ProviderError):
        _parse(bad, "car")
