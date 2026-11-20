import re

_FA = re.compile(r"[\u0600-\u06FF\u0750-\u077F]")
_LATIN = re.compile(r"[A-Za-z]")


def detect_language(text: str, default: str = "fa") -> str:
    """'fa' or 'en' by counting letters. Falls back to `default` if the text has no letters."""
    fa, en = len(_FA.findall(text)), len(_LATIN.findall(text))
    if fa == 0 and en == 0:
        return default
    return "fa" if fa >= en else "en"
