from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db, init_db
from .admin import setup_admin
from .routers import opportunities, places, routes

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env == "dev":
        init_db()
    yield


app = FastAPI(title="HARAKO API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET"],  # read-only public API for now
    allow_headers=["*"],
)

# The frontend's NEXT_PUBLIC_API_BASE_URL should point to  http(s)://host:8000/v1
app.include_router(places.router, prefix="/v1", tags=["places"])
app.include_router(opportunities.router, prefix="/v1", tags=["opportunities"])
app.include_router(routes.router, prefix="/v1", tags=["routes"])


setup_admin(app)  # /admin (stays off until ADMIN_* settings exist)


@app.get("/health", tags=["system"])
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
