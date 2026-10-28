"""Mo FastAPI application entry (aligned to openapi-v1 / memsSchemaVersion 1.0.0)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.db import db_status, init_db
from app.routers import auth, drive, health, history, jobs, materials, mems, projects, solver


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


def _normalize_http_detail(detail) -> dict:
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        return detail
    if isinstance(detail, str):
        return {"code": "error", "message": detail}
    return {"code": "error", "message": str(detail)}


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Mo motor multi-physics design platform API (Q1/Q2). "
            "Aligned with docs/drafts/openapi-v1.yaml (1.0.0; Q5-5 pin). "
            "Auth is Bearer-token placeholder; materials seed (Q2-1); analytic jobs optional Celery (Q2-6); projects CRUD uses Postgres when "
            "DATABASE_URL is reachable, else memory."
        ),
        lifespan=lifespan,
    )

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
        body = _normalize_http_detail(exc.detail)
        headers = getattr(exc, "headers", None) or {}
        return JSONResponse(status_code=exc.status_code, content=body, headers=headers)

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "code": "validation_error",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            },
        )

    application.include_router(health.router)
    application.include_router(auth.router)
    application.include_router(projects.router)
    application.include_router(mems.router)
    application.include_router(history.router)
    application.include_router(materials.router)
    application.include_router(jobs.router)
    application.include_router(drive.router)
    application.include_router(solver.router)
    return application


app = create_app()
