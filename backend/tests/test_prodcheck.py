from types import SimpleNamespace

from app.admin_auth import hash_password
from app.prodcheck import assert_production_ready, production_problems, production_warnings
import pytest

SECRET = "s" * 40


def good(**over):
    base = dict(
        app_env="prod",
        database_url="postgresql+psycopg://u:p@db/harako",
        cors_origin_list=["https://harako.example"],
        expose_sample_data=False,
        web_concurrency=2,
        redis_url="redis://redis:6379/0",
        tools_enabled=True,
        tools_api_key="k" * 24,
        admin_username="boss",
        admin_password="",
        admin_password_hash=hash_password("a-long-password-123", iterations=1000),
        admin_secret_key=SECRET,
        admin_cookie_secure=None,
        neshan_service_key="x",
    )
    base.update(over)
    return SimpleNamespace(**base)


def has(problems, text):
    return any(text in p for p in problems)


def test_dev_and_test_never_block():
    assert production_problems(good(app_env="dev", database_url="sqlite:///x.db", expose_sample_data=True)) == []


def test_good_config_passes():
    assert production_problems(good()) == []
    assert_production_ready(good())


def test_each_unsafe_setting_is_reported():
    assert has(production_problems(good(database_url="sqlite:///x.db")), "PostgreSQL")
    assert has(production_problems(good(cors_origin_list=[])), "CORS_ORIGINS is empty")
    assert has(production_problems(good(cors_origin_list=["*"])), "'*'")
    assert has(production_problems(good(cors_origin_list=["http://harako.example"])), "plain-http")
    assert has(production_problems(good(expose_sample_data=True)), "EXPOSE_SAMPLE_DATA")
    assert has(production_problems(good(redis_url="")), "REDIS_URL")
    assert has(production_problems(good(tools_api_key="")), "TOOLS_API_KEY")
    assert has(production_problems(good(admin_secret_key="short")), "ADMIN_SECRET_KEY")
    assert has(production_problems(good(admin_cookie_secure=False)), "ADMIN_COOKIE_SECURE")


def test_plaintext_admin_password_is_rejected_in_prod():
    p = production_problems(good(admin_password="a-long-password-123", admin_password_hash=""))
    assert has(p, "ADMIN_PASSWORD_HASH")


def test_capacitor_origins_are_allowed():
    assert production_problems(good(cors_origin_list=["https://harako.example", "https://localhost", "capacitor://localhost"])) == []


def test_single_worker_without_redis_is_allowed_but_warned():
    s = good(web_concurrency=1, redis_url="")
    assert production_problems(s) == []
    assert has(production_warnings(s), "REDIS_URL")


def test_assert_raises_with_all_problems():
    with pytest.raises(RuntimeError) as e:
        assert_production_ready(good(expose_sample_data=True, tools_api_key=""))
    assert "EXPOSE_SAMPLE_DATA" in str(e.value) and "TOOLS_API_KEY" in str(e.value)


def test_no_secret_values_in_messages():
    msgs = " ".join(production_problems(good(admin_secret_key="short", admin_password="plainpassword12", admin_password_hash="")))
    assert "plainpassword12" not in msgs and "short" not in msgs
