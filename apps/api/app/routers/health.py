"""Process health endpoint. Optional db/redis probes never fail the main path."""

from typing import Any

from fastapi import APIRouter

from app.db import probe_db
from app.redis_probe import probe_redis

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Liveness / process health",
    description="Always returns status=ok if the API process is up. "
    "db and redis are optional probes; failures do not change HTTP 200.",
)
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "db": probe_db(),
        "redis": probe_redis(),
    }
