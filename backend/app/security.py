"""ASGI middleware: CSRF defence for the admin panel.

Layers: (1) the session cookie is SameSite=Strict (see admin.py), (2) this guard refuses unsafe-method
requests to /admin whose Origin/Referer is not our own host. This is an Origin check, not a token
scheme: it is robust against ordinary cross-site forms/fetches in current browsers, but it is not a
substitute for keeping the admin on its own HTTPS host."""
from typing import Iterable

from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse

from .security_utils import origin_allowed

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class AdminOriginGuard:
    def __init__(self, app, prefix: str = "/admin", extra_hosts: Iterable[str] = ()):
        self.app = app
        self.prefix = prefix.rstrip("/")
        self.extra_hosts = tuple(extra_hosts)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"] in UNSAFE_METHODS:
            path = scope.get("path", "")
            if path == self.prefix or path.startswith(self.prefix + "/"):
                h = Headers(scope=scope)
                if not origin_allowed(h.get("origin"), h.get("referer"), h.get("host"), self.extra_hosts):
                    await PlainTextResponse("Cross-site request blocked", status_code=403)(scope, receive, send)
                    return
        await self.app(scope, receive, send)
