from app.admin_auth import LoginLimiter, credentials_ok, validate_admin_config

GOOD = ("kivo", "a-long-password-1", "s" * 32)


def test_config_is_off_when_not_set():
    assert "not set" in validate_admin_config("", "", "")


def test_config_rejects_weak_values():
    assert validate_admin_config("", GOOD[1], GOOD[2])
    assert "ADMIN_PASSWORD" in validate_admin_config("kivo", "short", GOOD[2])
    assert "ADMIN_SECRET_KEY" in validate_admin_config("kivo", GOOD[1], "short")


def test_config_accepts_good_values():
    assert validate_admin_config(*GOOD) is None


def test_credentials():
    assert credentials_ok("kivo", "pw-ok", "kivo", "pw-ok")
    assert not credentials_ok("kivo", "pw-bad", "kivo", "pw-ok")
    assert not credentials_ok("other", "pw-ok", "kivo", "pw-ok")
    assert credentials_ok("کیوو", "رمز-فارسی-۱۲۳", "کیوو", "رمز-فارسی-۱۲۳")  # non-ASCII works


def test_limiter_blocks_after_failures_and_recovers():
    lim = LoginLimiter(max_failures=3, window_s=60)
    for t in (0, 1, 2):
        assert not lim.blocked("1.1.1.1", now=t)
        lim.record_failure("1.1.1.1", now=t)
    assert lim.blocked("1.1.1.1", now=3)
    assert not lim.blocked("2.2.2.2", now=3)  # other clients are not affected
    assert not lim.blocked("1.1.1.1", now=100)  # window passed


def test_limiter_reset_after_success():
    lim = LoginLimiter(max_failures=2, window_s=60)
    lim.record_failure("a", now=0)
    lim.record_failure("a", now=1)
    assert lim.blocked("a", now=2)
    lim.reset("a")
    assert not lim.blocked("a", now=2)
