"""Mo FastAPI application entry (Q1-1)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.db import db_status, init_db
from app.routers import health, projects


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ok = init_db()
    status = db_status()
    if ok:
        print("[mo-api] Postgres connected; using SQLAlchemy store")
    else:
        print(
            "[mo-api] Postgres unavailable — using in-memory project store. "
            f"error={status.get('error')}"
        )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Mo motor multi-physics design platform API (Q1-1 shell). "
            "Auth is Bearer-token placeholder; projects CRUD uses Postgres when "
            "DATABASE_URL is reachable (host 127.0.0.1:5433), else memory."
        ),
        lifespan=lifespan,
    )
    application.include_router(health.router)
    application.include_router(projects.router)
    return application


app = create_app()
