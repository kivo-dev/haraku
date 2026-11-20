"""Admin panel at /admin (SQLAdmin). One admin, login from .env.

It stays OFF until ADMIN_USERNAME, ADMIN_PASSWORD and ADMIN_SECRET_KEY are set (see .env.example),
so a forgotten setting can never leave an open admin door.
"""
import logging

from fastapi import FastAPI

from .admin_auth import LoginLimiter, credentials_ok, validate_admin_config
from .config import get_settings

log = logging.getLogger("harako.admin")

STATUS_CHOICES = [("draft", "draft (hidden)"), ("published", "published (visible)"), ("inactive", "inactive (hidden)")]
VERIFY_CHOICES = [("unverified", "unverified"), ("verified", "verified")]


def setup_admin(app: FastAPI) -> None:
    s = get_settings()
    problem = validate_admin_config(s.admin_username, s.admin_password, s.admin_secret_key)
    if problem:
        log.warning("Admin panel is OFF: %s", problem)
        return

    from sqladmin import Admin, ModelView
    from sqladmin.authentication import AuthenticationBackend
    from starlette.requests import Request

    from .db import engine
    from .models import Category, Opportunity, Place, PlaceImage

    limiter = LoginLimiter(max_failures=5, window_s=600)

    class AdminAuth(AuthenticationBackend):
        async def login(self, request: Request) -> bool:
            ip = request.client.host if request.client else "unknown"
            if limiter.blocked(ip):
                return False
            form = await request.form()
            ok = credentials_ok(str(form.get("username", "")), str(form.get("password", "")), s.admin_username, s.admin_password)
            if not ok:
                limiter.record_failure(ip)
                return False
            limiter.reset(ip)
            request.session.update({"admin": True})
            return True

        async def logout(self, request: Request) -> bool:
            request.session.clear()
            return True

        async def authenticate(self, request: Request) -> bool:
            return bool(request.session.get("admin"))

    admin = Admin(app, engine, authentication_backend=AdminAuth(secret_key=s.admin_secret_key), title="HARAKO مدیریت")

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
