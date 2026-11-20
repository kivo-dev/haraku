from app.scoring import Candidate, suggest


def make(n, cat="nature", **kw):
    return Candidate(id=f"p{n}", category=cat, **kw)


def test_limit_and_no_duplicates():
    cands = [make(i, cat=["nature", "history", "services"][i % 3]) for i in range(10)]
    out = suggest(cands, limit=6, seed=1)
    ids = [s.candidate.id for s in out]
    assert len(ids) == 6 and len(set(ids)) == 6


def test_fewer_candidates_than_limit():
    assert len(suggest([make(1), make(2)], limit=6, seed=1)) == 2
    assert suggest([], limit=6) == []


def test_same_seed_same_result_different_seed_can_differ():
    cands = [make(i, cat=["nature", "history", "services"][i % 3]) for i in range(12)]
    a = [s.candidate.id for s in suggest(cands, limit=6, seed=7)]
    b = [s.candidate.id for s in suggest(cands, limit=6, seed=7)]
    assert a == b
    others = {tuple(s.candidate.id for s in suggest(cands, limit=6, seed=k)) for k in range(30)}
    assert len(others) > 1  # refreshing really gives something new


def test_featured_wins_when_everything_else_is_equal():
    cands = [make(1, featured=True), make(2), make(3)]
    # jitter max 1.5 < featured bonus 3.0, so the featured place is always first
    for seed in range(20):
        assert suggest(cands, limit=3, seed=seed)[0].candidate.id == "p1"


def test_variety_across_categories():
    cands = [make(i, cat="nature", featured=True) for i in range(5)] + [make(9, cat="history"), make(10, cat="services")]
    for seed in range(50):
        out = suggest(cands, limit=3, seed=seed)
        assert {s.candidate.category for s in out} == {"nature", "history", "services"}


def test_recently_shown_are_pushed_down():
    cands = [make(1, featured=True), make(2, featured=True), make(3, featured=True)]
    for seed in range(10):
        out = suggest(cands, limit=3, seed=seed, exclude=["p1"])
        assert out[-1].candidate.id == "p1"


def test_proximity_and_honest_reason():
    near = make(1, lat=39.30, lng=44.50)
    far = make(2, lat=39.90, lng=45.50)
    out = suggest([near, far], limit=2, user=(39.29, 44.51), seed=0)
    by_id = {s.candidate.id: s for s in out}
    assert by_id["p1"].reason == "near" and by_id["p1"].distance_km < 5
    assert by_id["p2"].reason is None  # far and not featured: no claim is made
    # no position given -> never claims "near"
    assert all(s.reason != "near" for s in suggest([near, far], limit=2, seed=0))
