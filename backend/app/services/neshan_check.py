"""One real call to Neshan, printing the RAW answer, to verify the adapter against the docs.

    python -m app.services.neshan_check 39.29,44.51 39.39,44.38

Needs NESHAN_SERVICE_KEY in .env. Do not paste the key anywhere; paste only the printed JSON
(it contains no key)."""
import json
import sys

import httpx

from ..config import get_settings
from .neshan import BASE_URL, DIRECTION_PATH, ProviderError, _parse


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: python -m app.services.neshan_check LAT,LNG LAT,LNG")
    key = get_settings().neshan_service_key
    if not key:
        sys.exit("NESHAN_SERVICE_KEY is empty (.env)")
    res = httpx.get(
        BASE_URL + DIRECTION_PATH,
        params={"type": "car", "origin": sys.argv[1], "destination": sys.argv[2]},
        headers={"Api-Key": key},
        timeout=10,
    )
    print("HTTP status:", res.status_code)
    try:
        data = res.json()
    except ValueError:
        print(res.text[:500])
        return
    print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    try:
        print("PARSED:", _parse(data, "car"))
    except ProviderError as exc:
        print("PARSE FAILED:", exc, "-> adjust _parse() in neshan.py")


if __name__ == "__main__":
    main()
