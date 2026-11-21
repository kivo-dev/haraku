"""Test setup. Environment is fixed BEFORE the app is imported, so a developer's real .env can never leak
into tests (real environment variables beat the .env file)."""
import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="harako-test-")
os.environ.update(
    {
        "APP_ENV": "test",
        "DATABASE_URL": f"sqlite:///{_TMP}/test.db",
        "CORS_ORIGINS": "http://localhost:3000",
        "EXPOSE_SAMPLE_DATA": "true",
        "NESHAN_SERVICE_KEY": "",
        "ADMIN_USERNAME": "",
        "ADMIN_PASSWORD": "",
        "ADMIN_PASSWORD_HASH": "",
        "ADMIN_SECRET_KEY": "",
        "TOOLS_API_KEY": "",
        "TOOLS_ENABLED": "true",
        "REDIS_URL": "",
        "TRUSTED_PROXY_COUNT": "0",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, Category, Opportunity, Place  # noqa: E402
from app.providers.base import RouteResult  # noqa: E402
from app.providers.registry import get_routing_provider  # noqa: E402
from app.ratelimit import get_store  # noqa: E402


class FakeRouting:
    """Stands in for the unverified Neshan adapter."""

    def __init__(self):
        self.calls = []

    async def route(self, origin, destination, mode="car"):
        self.calls.append((origin, destination, mode))
        return RouteResult("fake", mode, 1234, 600, "encoded-polyline")


@pytest.fixture(autouse=True)
def fresh_db_and_limits():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    get_store.cache_clear()
    yield
    app.dependency_overrides.clear()
    get_store.cache_clear()


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def fake_routing():
    fake = FakeRouting()
    app.dependency_overrides[get_routing_provider] = lambda: fake
    return fake


def _place(pid, **kw):
    base = dict(
        id=pid, category_key="nature", name_fa=f"نام {pid}", name_en=f"Name {pid}", area_fa="ماکو", area_en="Maku",
        summary_fa="خلاصه", summary_en="summary", status="published", verification="verified", source="manual",
    )
    base.update(kw)
    return Place(**base)


@pytest.fixture
def seeded():
    with SessionLocal() as db:
        db.add_all([Category(key="nature", title_fa="طبیعت", title_en="Nature", sort=1),
                    Category(key="history", title_fa="تاریخی", title_en="History", sort=2)])
        db.flush()
        db.add_all(
            [
                _place("near", lat=39.30, lng=44.50, featured=True),
                _place("mid", lat=39.40, lng=44.60, category_key="history", verification="unverified"),
                _place("far", lat=40.50, lng=45.50),
                _place("no-coords"),
                _place("draft", lat=39.30, lng=44.51, status="draft"),
                _place("sample", lat=39.301, lng=44.501, source="seed-sample"),
                Opportunity(id="o1", sector="trade", title_fa="تجارت", title_en="Trade", status="published"),
                Opportunity(id="o-sample", sector="trade", title_fa="نمونه", title_en="Sample", status="published", source="seed-sample"),
            ]
        )
        db.commit()
