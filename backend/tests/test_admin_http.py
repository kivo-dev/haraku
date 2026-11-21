"""Admin panel over HTTP (needs sqladmin). Builds its own small app with the admin enabled."""
import pytest

pytest.importorskip("sqladmin")
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.admin as admin_mod  # noqa: E402
from app.admin_auth import hash_password  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.ratelimit import get_store  # noqa: E402
from app.security import AdminOriginGuard  # noqa: E402

PASSWORD = "a-long-admin-password-1"


def make_client(monkeypatch, scheme="http", **over):
    s = get_settings().model_copy(update={
        "admin_username": "boss", "admin_password": "", "admin_password_hash": hash_password(PASSWORD, iterations=1000),
        "admin_secret_key": "k" * 40, "admin_cookie_secure": scheme == "https", **over,
    })
    monkeypatch.setattr(admin_mod, "get_settings", lambda: s)
    get_store.cache_clear()
    app = FastAPI()
    app.add_middleware(AdminOriginGuard, prefix="/admin")
    admin_mod.setup_admin(app)
    return TestClient(app, base_url=f"{scheme}://testserver", follow_redirects=False), f"{scheme}://testserver"


def login(c, origin, password=PASSWORD, username="boss"):
    return c.post("/admin/login", data={"username": username, "password": password}, headers={"Origin": origin})


def test_wrong_password_is_rejected_and_good_password_redirects(monkeypatch):
    c, o = make_client(monkeypatch)
    assert login(c, o, "wrong-password-xx").status_code not in (302, 303)
    assert login(c, o).status_code in (302, 303)
    assert c.get("/admin/").status_code == 200  # session cookie accepted


def test_unauthenticated_admin_redirects_to_login(monkeypatch):
    c, _ = make_client(monkeypatch)
    r = c.get("/admin/")
    assert r.status_code in (302, 303) and "/admin/login" in r.headers["location"]


def test_login_blocked_after_too_many_failures(monkeypatch):
    c, o = make_client(monkeypatch, admin_login_max_failures=3)
    for _ in range(3):
        login(c, o, "wrong-password-xx")
    assert login(c, o).status_code not in (302, 303)  # even the right password is refused while blocked


def test_cross_site_post_is_blocked(monkeypatch):
    c, _ = make_client(monkeypatch)
    r = c.post("/admin/login", data={"username": "boss", "password": PASSWORD}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    assert c.post("/admin/login", data={"username": "boss", "password": PASSWORD}).status_code == 403  # no Origin/Referer


def test_session_cookie_flags(monkeypatch):
    c, o = make_client(monkeypatch, scheme="https")
    cookie = login(c, o).headers["set-cookie"].lower()
    assert "harako_admin=" in cookie and "httponly" in cookie and "samesite=strict" in cookie and "secure" in cookie
    assert "max-age=" in cookie


def test_admin_off_without_valid_config(monkeypatch):
    s = get_settings().model_copy(update={"admin_username": "", "admin_password": "", "admin_password_hash": "", "admin_secret_key": ""})
    monkeypatch.setattr(admin_mod, "get_settings", lambda: s)
    app = FastAPI()
    admin_mod.setup_admin(app)
    assert TestClient(app).get("/admin/").status_code == 404
