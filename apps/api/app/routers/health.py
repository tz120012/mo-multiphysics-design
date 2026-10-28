"""Health endpoints: OpenAPI GET /api/v1/health + root /health probe alias."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app.config import get_settings
from app.db import probe_db
from app.redis_probe import probe_redis

router = APIRouter(tags=["Health"])


def _health_payload() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "version": settings.app_version,
        "time": datetime.now(timezone.utc).isoformat(),
        # Extra probes (not in OpenAPI Health schema; harmless for clients)
        "db": probe_db(),
        "redis": probe_redis(),
    }


@router.get(
    "/api/v1/health",
    summary="Liveness / readiness probe (contract path)",
    description="OpenAPI servers.url=/api/v1 → GET /api/v1/health. "
    "Always returns status=ok if the API process is up.",
)
def health_v1() -> dict[str, Any]:
    return _health_payload()


@router.get(
    "/health",
    summary="Liveness probe alias (root)",
    description="Same handler as /api/v1/health for compose/k8s probes. "
    "Prefer /api/v1/health for API clients.",
    include_in_schema=True,
)
def health_root() -> dict[str, Any]:
    return _health_payload()
