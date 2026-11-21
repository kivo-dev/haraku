from app.ratestore import FallbackStore, MemoryStore, RedisStore, pick_client_ip


class FakeRedis:
    def __init__(self):
        self.data, self.expires = {}, []

    def incr(self, k):
        self.data[k] = self.data.get(k, 0) + 1
        return self.data[k]

    def expire(self, k, s):
        self.expires.append((k, s))

    def get(self, k):
        return self.data.get(k)

    def delete(self, k):
        self.data.pop(k, None)


class BrokenRedis:
    def __getattr__(self, name):
        def boom(*a, **k):
            raise ConnectionError("redis down")
        return boom


def test_memory_counts_and_window():
    s = MemoryStore()
    assert s.hit("k", 60, now=0) == 1
    assert s.hit("k", 60, now=10) == 2
    assert s.count("k", 60, now=20) == 2
    assert s.count("k", 60, now=65) == 1  # the first hit is older than 60 s
    assert s.count("k", 60, now=100) == 0


def test_memory_keys_are_independent_and_clear_works():
    s = MemoryStore()
    s.hit("a", 60, now=0)
    s.hit("b", 60, now=0)
    s.clear("a")
    assert s.count("a", 60, now=1) == 0
    assert s.count("b", 60, now=1) == 1


def test_redis_store_sets_expiry_only_on_first_hit():
    r = FakeRedis()
    s = RedisStore(r)
    assert [s.hit("k", 60) for _ in range(3)] == [1, 2, 3]
    assert r.expires == [("harako:rl:k", 60)]
    assert s.count("k", 60) == 3
    s.clear("k")
    assert s.count("k", 60) == 0


def test_fallback_uses_memory_when_redis_is_down():
    s = FallbackStore(RedisStore(BrokenRedis()))
    assert s.hit("k", 60) == 1
    assert s.hit("k", 60) == 2
    assert s.count("k", 60) == 2
    s.clear("k")
    assert s.count("k", 60) == 0


def test_client_ip_ignores_header_without_trusted_proxy():
    assert pick_client_ip("1.1.1.1", "9.9.9.9", 0) == "9.9.9.9"
    assert pick_client_ip(None, None, 0) == "unknown"


def test_client_ip_uses_nth_entry_from_the_right():
    # attacker sends "6.6.6.6"; our one trusted proxy appends the real client 2.2.2.2
    assert pick_client_ip("6.6.6.6, 2.2.2.2", "10.0.0.1", 1) == "2.2.2.2"
    assert pick_client_ip("6.6.6.6, 2.2.2.2, 10.0.0.5", "10.0.0.1", 2) == "2.2.2.2"
    assert pick_client_ip("2.2.2.2", "10.0.0.1", 3) == "10.0.0.1"  # header shorter than expected: do not trust
