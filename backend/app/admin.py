"""Admin panel at /admin (SQLAdmin). One admin, login from .env.

It stays OFF until ADMIN_USERNAME, ADMIN_PASSWORD (or ADMIN_PASSWORD_HASH) and ADMIN_SECRET_KEY are set,
so a forgotten setting can never leave an open admin door.
"""
import logging

from fastapi import FastAPI

from .admin_auth import StoreLoginLimiter, check_login, validate_admin_config
from .config import get_settings

log = logging.getLogger("harako.admin")

STATUS_CHOICES = [("draft", "draft (hidden)"), ("published", "published (visible)"), ("inactive", "inactive (hidden)")]
VERIFY_CHOICES = [("unverified", "unverified"), ("verified", "verified")]


def setup_admin(app: FastAPI) -> None:
    s = get_settings()
    problem = validate_admin_config(s.admin_username, s.admin_password, s.admin_secret_key, s.admin_password_hash)
    if problem:
        log.warning("Admin panel is OFF: %s", problem)
        return

    from sqladmin import Admin, ModelView
    from sqladmin.authentication import AuthenticationBackend
    from starlette.middleware import Middleware
    from starlette.middleware.sessions import SessionMiddleware
    from starlette.requests import Request

    from .db import engine
    from .models import Category, Opportunity, Place, PlaceImage
    from .ratelimit import client_ip, get_store

    limiter = StoreLoginLimiter(get_store(), s.admin_login_max_failures, s.admin_login_window_s)

    class AdminAuth(AuthenticationBackend):
        def __init__(self) -> None:
            super().__init__(secret_key=s.admin_secret_key)
            # Replace sqladmin's default session middleware so the cookie gets explicit security flags:
            # HttpOnly (always), SameSite=Strict, Secure (prod/HTTPS), a dedicated name and a lifetime
            # that is also enforced server-side by the signed timestamp.
            self.middlewares = [
                Middleware(
                    SessionMiddleware,
                    secret_key=s.admin_secret_key,
                    session_cookie="harako_admin",
                    max_age=s.admin_session_max_age_s,
                    same_site="strict",
                    https_only=s.admin_cookie_https_only,
                )
            ]

        async def login(self, request: Request) -> bool:
            ip = client_ip(request)
            if limiter.blocked(ip):
                log.warning("Admin login blocked (too many failures)")
                return False
            form = await request.form()
            ok = check_login(
                str(form.get("username", "")),
                str(form.get("password", "")),
                s.admin_username,
                s.admin_password,
                s.admin_password_hash,
            )
            if not ok:
                limiter.record_failure(ip)
                return False
            limiter.reset(ip)
            request.session.clear()  # fresh session on every login (no session fixation)
            request.session.update({"admin": True})
            return True

        async def logout(self, request: Request) -> bool:
            request.session.clear()
            return True

        async def authenticate(self, request: Request) -> bool:
            return bool(request.session.get("admin"))

    admin = Admin(app, engine, authentication_backend=AdminAuth(), title="HARAKO مدیریت")

    class PlaceAdmin(ModelView, model=Place):
        name = "مکان"
        name_plural = "مکان‌ها"
        icon = "fa-solid fa-location-dot"
        column_list = ["id", "name_fa", "category", "status", "verification", "featured", "lat", "lng"]
        column_searchable_list = ["id", "name_fa", "name_en", "area_fa"]
        column_sortable_list = ["id", "name_fa", "status", "featured", "updated_at"]
        column_default_sort = [("updated_at", True)]
        form_columns = [
            "id", "category", "name_fa", "name_en", "area_fa", "area_en", "summary_fa", "summary_en",
            "lat", "lng", "rating", "featured", "status", "verification", "source", "image_url",
        ]
        form_choices = {"status": STATUS_CHOICES, "verification": VERIFY_CHOICES}
        can_export = False
        page_size = 50

    class PlaceImageAdmin(ModelView, model=PlaceImage):
        name = "عکس مکان"
        name_plural = "عکس‌های مکان"
        icon = "fa-solid fa-image"
        column_list = ["id", "place", "url", "sort"]
        form_columns = ["place", "url", "caption_fa", "caption_en", "sort"]
        can_export = False

    class OpportunityAdmin(ModelView, model=Opportunity):
        name = "فرصت اقتصادی"
        name_plural = "فرصت‌های اقتصادی"
        icon = "fa-solid fa-briefcase"
        column_list = ["id", "sector", "title_fa", "status", "verification"]
        column_searchable_list = ["id", "title_fa", "title_en"]
        form_columns = [
            "id", "sector", "title_fa", "title_en", "summary_fa", "summary_en",
            "status", "verification", "source", "image_url",
        ]
        form_choices = {
            "status": STATUS_CHOICES,
            "verification": VERIFY_CHOICES,
            "sector": [(k, k) for k in ("trade", "industry", "agriculture", "tourism")],
        }
        can_export = False

    class CategoryAdmin(ModelView, model=Category):
        name = "دسته"
        name_plural = "دسته‌ها"
        icon = "fa-solid fa-tags"
        column_list = ["key", "title_fa", "title_en", "sort"]
        form_columns = ["key", "title_fa", "title_en", "sort"]
        can_export = False

    for view in (PlaceAdmin, PlaceImageAdmin, OpportunityAdmin, CategoryAdmin):
        admin.add_view(view)
    log.info("Admin panel is ON at /admin")
