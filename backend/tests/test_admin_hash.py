from app.admin_auth import (
    StoreLoginLimiter,
    check_login,
    hash_password,
    validate_admin_config,
    verify_password,
)
from app.ratestore import MemoryStore

H = hash_password("correct horse battery", iterations=1000)


def test_hash_roundtrip_and_format():
    assert H.startswith("pbkdf2_sha256$1000$")
    assert verify_password("correct horse battery", H)
    assert not verify_password("wrong", H)


def test_hashes_are_salted():
    assert hash_password("same-password-1", iterations=1000) != hash_password("same-password-1", iterations=1000)


def test_malformed_hash_never_verifies():
    for bad in ("", "plain", "a$b$c$d", "pbkdf2_sha256$x$AAAA$AAAA", "pbkdf2_sha256$0$AAAA$AAAA", "pbkdf2_sha256$10$!!$!!"):
        assert not verify_password("x", bad)


def test_check_login_with_hash_and_with_plaintext():
    assert check_login("boss", "correct horse battery", "boss", "", H)
    assert not check_login("boss", "nope", "boss", "", H)
    assert not check_login("other", "correct horse battery", "boss", "", H)
    assert check_login("boss", "plain-password-1", "boss", "plain-password-1", "")
    assert not check_login("boss", "x", "boss", "plain-password-1", "")


def test_hash_takes_precedence_over_plaintext():
    assert not check_login("boss", "plain-password-1", "boss", "plain-password-1", H)


def test_validate_accepts_hash_instead_of_password():
    assert validate_admin_config("boss", "", "s" * 40, H) is None
    assert "malformed" in validate_admin_config("boss", "", "s" * 40, "garbage")
    assert "ADMIN_PASSWORD" in validate_admin_config("boss", "short", "s" * 40)
    assert validate_admin_config("", "", "", "") is not None


def test_store_login_limiter_blocks_then_resets():
    lim = StoreLoginLimiter(MemoryStore(), max_failures=3, window_s=600)
    for _ in range(2):
        lim.record_failure("1.2.3.4")
    assert not lim.blocked("1.2.3.4")
    lim.record_failure("1.2.3.4")
    assert lim.blocked("1.2.3.4")
    assert not lim.blocked("5.6.7.8")
    lim.reset("1.2.3.4")
    assert not lim.blocked("1.2.3.4")
