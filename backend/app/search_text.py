"""Persian-friendly text normalisation for search.

Problem: the same Persian word is typed many ways (Arabic ي/ك, half-space, digits, diacritics).
Solution: store a normalised form next to every searchable record and normalise the query the same way.
Two forms are used:
  normalized  "قره کلیسا"  words separated by single spaces
  compact     "قرهکلیسا"   no spaces at all, so "قره کلیسا", "قره‌کلیسا" and "قرهکلیسا" all match each other
"""
import re
import unicodedata

_CHAR_MAP = str.maketrans(
    {
        "ي": "ی", "ى": "ی", "ئ": "ی",  # Arabic yeh forms -> Persian yeh
        "ك": "ک",  # Arabic kaf
        "ە": "ه", "ۀ": "ه", "ة": "ه",
        "أ": "ا", "إ": "ا", "ٱ": "ا", "آ": "ا",
        "ؤ": "و",
        # digits: Persian and Arabic-Indic -> ASCII
        **{chr(0x06F0 + i): str(i) for i in range(10)},
        **{chr(0x0660 + i): str(i) for i in range(10)},
    }
)
# diacritics (harakat), superscript alef, tatweel
_STRIP = re.compile("[ً-ٰٟـ]")
# zero-width joiners / directional marks: removed
_INVISIBLE = re.compile("[‍‎‏‪-‮⁦-⁩﻿]")
_NOT_WORD = re.compile(r"[^\w\s]", re.UNICODE)
_SPACES = re.compile(r"\s+")


def normalize(text: str | None) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFKC", text)
    s = s.replace("‌", " ")  # half-space (ZWNJ) acts as a word break
    s = _INVISIBLE.sub("", s)
    s = _STRIP.sub("", s)
    s = s.translate(_CHAR_MAP)
    s = s.lower()
    s = s.replace("_", " ")
    s = _NOT_WORD.sub(" ", s)
    return _SPACES.sub(" ", s).strip()


def compact(text: str | None) -> str:
    return normalize(text).replace(" ", "")


def build_search_fields(*texts: str | None) -> tuple[str, str]:
    """(normalized, compact) for everything searchable about one record."""
    joined = " ".join(t for t in texts if t)
    return normalize(joined), compact(joined)


def query_keys(q: str | None) -> tuple[str, str] | None:
    """(normalized, compact) for a user query, or None if it is empty after normalising."""
    n = normalize(q)
    if not n:
        return None
    return n, n.replace(" ", "")
