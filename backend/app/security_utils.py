"""Pure helpers for request-origin checks (CSRF defence for the admin panel)."""
from typing import Iterable, Optional
from urllib.parse import urlsplit


def origin_allowed(origin: Optional[str], referer: Optional[str], host: Optional[str], extra_hosts: Iterable[str] = ()) -> bool:
    """A state-changing admin request is accepted only when the browser says it came from our own host.
    Browsers always send `Origin` on cross-site POSTs; `Referer` is the fallback. Neither present = refuse."""
    source = origin if origin and origin != "null" else referer
    if not source:
        return False
    netloc = urlsplit(source).netloc.lower()
    if not netloc:
        return False
    if host and netloc == host.lower():
        return True
    return netloc in {h.lower() for h in extra_hosts}
