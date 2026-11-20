from app.search_text import build_search_fields, compact, normalize, query_keys


def test_arabic_letters_become_persian():
    assert normalize("كليسا") == normalize("کلیسا") == "کلیسا"


def test_half_space_and_space_match_each_other():
    assert normalize("قره‌کلیسا") == "قره کلیسا"
    assert compact("قره‌کلیسا") == compact("قره کلیسا") == compact("قرهکلیسا") == "قرهکلیسا"


def test_digits_and_case_and_diacritics():
    assert normalize("هتل ۵ ستاره") == "هتل 5 ستاره"
    assert normalize("هتل ٥ ستاره") == "هتل 5 ستاره"
    assert normalize("Maku  VIEWpoint!") == "maku viewpoint"
    assert normalize("مَاكُو") == "ماکو"


def test_empty_and_none():
    assert normalize(None) == "" and normalize("  ") == ""
    assert query_keys("   ") is None and query_keys(None) is None


def test_search_fields_and_query_find_each_other():
    n, c = build_search_fields("قره‌کلیسا", "Qareh Kelisa", None, "حوالی چالدران")
    qn, qc = query_keys("قره کليسا")
    assert qn in n or qc in c
    qn, qc = query_keys("qarehkelisa")
    assert qc in c
