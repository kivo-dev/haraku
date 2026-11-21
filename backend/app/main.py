import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from .admin import setup_admin
from .config import get_settings
from .db import get_db, init_db
from .logging_filters import RedactLocationFilter
from .prodcheck import assert_production_ready, production_warnings
from .providers.base import ProviderDisabled, ProviderError, ProviderNotImplemented
from .routers import geo, opportunities, places, routes, system, tools
from .security import AdminOriginGuard

settings = get_settings()
log = logging.getLogger("harako")

# uvicorn's access log prints full URLs; strip precise user coordinates from them.
logging.getLogger("uvicorn.access").addFilter(RedactLocationFilter())


@asynccontextmanager
async def lifespan(_: FastAPI):
    assert_production_ready(settings)  # prod: refuse to start on an unsafe configuration
    for w in production_warnings(settings):
        log.warning(w)
    if settings.app_env == "dev":
        init_db()
    yield


app = FastAPI(title="HARAKO API", version="0.2.0", lifespan=lifespan)

app.add_middleware(AdminOriginGuard, prefix="/admin", extra_hosts=settings.admin_allowed_origin_list)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET"],  # read-only public API
    allow_headers=["*"],  # TODO: narrow to the headers the frontend really sends, once its source is reviewed
)


@app.exception_handler(ProviderNotImplemented)
async def _not_implemented(_: Request, exc: ProviderNotImplemented):
    return JSONResponse(
        status_code=501,
        content={"detail": {"code": "provider_not_implemented", "provider": exc.provider, "capability": exc.capability, "message": exc.message}},
    )


@app.exception_handler(ProviderDisabled)
async def _disabled(_: Request, exc: ProviderDisabled):  # noqa: ARG001
    return JSONResponse(status_code=503, content={"detail": "This provider is not configured on the server"})


@app.exception_handler(ProviderError)
async def _provider_error(_: Request, exc: ProviderError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


# The frontend's NEXT_PUBLIC_API_BASE_URL should point to  http(s)://host:8000/v1
app.include_router(places.router, prefix="/v1", tags=["places"])
app.include_router(opportunities.router, prefix="/v1", tags=["opportunities"])
app.include_router(routes.router, prefix="/v1", tags=["routes"])
app.include_router(geo.router, prefix="/v1", tags=["geo (neshan pending)"])
app.include_router(system.router, prefix="/v1", tags=["system"])
app.include_router(tools.router, prefix="/v1", tags=["ai-tools"])


setup_admin(app)  # /admin (stays off until ADMIN_* settings exist)


@app.get("/health", tags=["system"])
def health(db: Session = Depends(get_db)):
    """Readiness: the database answers."""
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/health/live", tags=["system"])
def health_live():
    """Liveness: the process is up (no database call). Used by the Docker healthcheck."""
    return {"status": "ok"}
